# merge.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Finds design topics that describe one subject, and merges one topic into another.

`overlap` lists the modules two topics name and the topics whose names share a word. `merge`
makes the merged topic a page of the other, joins the phase tables and the modules, deletes the
merged folder and rewrites every citation of it.
"""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from ..citations import Rewrite, repair_citations
from .errors import DesignError
from .model import (
    K_CLOSED_PHASE_STATES,
    K_FIELD,
    Phase,
    open_status,
    replace_phases,
    replace_status,
)
from .store import K_README, DesignStore, Topic

K_NAME_WORD = re.compile(r"[A-Z0-9]+")
K_SHORT_WORD = 3
K_COMMON_WORDS = frozenset({"AND", "THE", "FOR", "SYSTEM", "SYSTEMS", "TOOL", "TOOLS", "MODEL"})
K_GENERATED_BLOCK = re.compile(r"<!-- (\w+):begin -->.*?<!-- \1:end -->\n?", re.DOTALL)


@dataclass(frozen=True, slots=True)
class Overlap:
    """What `overlap` found: shared modules, nested modules and names that share a word."""

    shared: tuple[tuple[str, tuple[str, ...]], ...]
    nested: tuple[tuple[str, str, str, str], ...]
    words: tuple[tuple[str, str, str], ...]


@dataclass(frozen=True, slots=True)
class MergeResult:
    """What `merge` did: the page it wrote, the files it moved, the phase ids and the citations."""

    page: Path
    moved: tuple[tuple[str, str], ...]
    renamed_phases: tuple[tuple[str, str], ...]
    rewrites: tuple[Rewrite, ...]


def find_overlap(store: DesignStore) -> Overlap:
    """Returns every module two topics name, every module inside another's, and shared name words."""
    owners = store.owners()
    shared = tuple((module, tuple(names)) for module, names in sorted(owners.items()) if len(names) > 1)
    nested: list[tuple[str, str, str, str]] = []
    for outer, outer_names in sorted(owners.items()):
        for inner, inner_names in sorted(owners.items()):
            if PurePosixPath(outer) in PurePosixPath(inner).parents:
                nested += [(outer, a, inner, b) for a in outer_names for b in inner_names if a != b]
    names = sorted(store.topic_paths())
    words: list[tuple[str, str, str]] = []
    for index, first in enumerate(names):
        for second in names[index + 1:]:
            common = _words(first) & _words(second)
            words += [(first, second, word) for word in sorted(common)]
    return Overlap(shared, tuple(nested), tuple(words))


class TopicMerger:
    """Merges one topic of a store into another."""

    def __init__(self, store: DesignStore) -> None:
        """Keeps the store whose topics are merged."""
        self.store = store

    def merge(self, into: str, source: str) -> MergeResult:
        """Makes *source* a page of *into* and deletes it.

        @throws DesignError When the topics are the same, *into* is a loose file, or a page of
            the merged topic's name exists.
        """
        if into == source:
            raise DesignError("a topic is not merged into itself")
        target, merged = self.store.topic(into), self.store.topic(source)
        if target.path.name != K_README:
            raise DesignError(f"{into} is a loose file; give it its folder first")
        folder = target.path.parent
        page = folder / f"{source}.md"
        if page.exists():
            raise DesignError(f"{page} exists")
        moves, renames = self._move_pages(merged, folder)
        moves[self.store.relative(merged.path)] = self.store.relative(page)
        if merged.path.name == K_README:
            moves[self.store.relative(merged.path.parent)] = self.store.relative(page)
        phases, phase_renames = _joined_phases(target, merged)
        page_text = _page_text(merged)
        for old, new in renames.items():
            page_text = page_text.replace(f"]({old}", f"]({new}")
        self.store.write_file(page, page_text)
        text = replace_phases(target.path.read_text(encoding="utf-8-sig"), phases)
        if any(phase.state not in K_CLOSED_PHASE_STATES for phase in phases) and not target.document.is_open():
            text = replace_status(text, open_status(phases))
        self.store.write_file(target.path, text)
        modules = list(dict.fromkeys([*(target.document.modules() or []), *(merged.document.modules() or [])]))
        self.store.set_modules(into, modules)
        if merged.path.name == K_README:
            shutil.rmtree(merged.path.parent)
        else:
            merged.path.unlink()
        self._rename_references(source, into, phase_renames)
        rewrites = repair_citations(self.store.root, self.store.topic_paths(), moves, apply=True)
        return MergeResult(page, tuple(moves.items()), tuple(phase_renames.items()), tuple(rewrites))

    def _move_pages(self, merged: Topic, folder: Path) -> tuple[dict[str, str], dict[str, str]]:
        """Moves the pages beside the merged README into *folder*; returns the moves and the renames."""
        moves: dict[str, str] = {}
        renames: dict[str, str] = {}
        if merged.path.name != K_README:
            return moves, renames
        for path in sorted(merged.path.parent.rglob("*")):
            if not path.is_file() or path == merged.path:
                continue
            relative = path.relative_to(merged.path.parent)
            destination = folder / relative
            if destination.exists():
                destination = folder / f"{merged.name}_{relative.as_posix().replace('/', '_')}"
                renames[relative.as_posix()] = destination.name
            destination.parent.mkdir(parents=True, exist_ok=True)
            moves[self.store.relative(path)] = self.store.relative(destination)
            shutil.move(str(path), str(destination))
        return moves, renames

    def _rename_references(self, source: str, into: str, phases: dict[str, str]) -> None:
        """Rewrites `SOURCE#PHASE` and `Designs: SOURCE` in every work folder's first file."""
        pattern = re.compile(rf"(?<![A-Z0-9_]){re.escape(source)}(?:#(?P<phase>[A-Za-z0-9_.-]+))?(?![A-Z0-9_])")

        def replace(match: re.Match[str]) -> str:
            """Returns the reference to the topic the merged one became part of."""
            phase = match["phase"]
            return into if phase is None else f"{into}#{phases.get(phase, phase)}"

        for path in self.store.work_documents():
            lines = path.read_text(encoding="utf-8").split("\n")
            changed = False
            for index, line in enumerate(lines):
                field = K_FIELD.match(line)
                if field and field["name"] in ("Implements", "Designs"):
                    new = pattern.sub(replace, line)
                    changed |= new != line
                    lines[index] = new
            if changed:
                path.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def _joined_phases(target: Topic, merged: Topic) -> tuple[list[Phase], dict[str, str]]:
    """Returns the target's phases followed by the merged ones, a clashing id prefixed by its topic."""
    taken = {phase.ident for phase in target.document.phases}
    phases = list(target.document.phases)
    renames: dict[str, str] = {}
    for phase in merged.document.phases:
        ident = phase.ident if phase.ident not in taken else f"{merged.name}-{phase.ident}"
        if ident != phase.ident:
            renames[phase.ident] = ident
        taken.add(ident)
        phases.append(Phase(ident, phase.text, phase.state))
    return phases, renames


def _page_text(merged: Topic) -> str:
    """Returns the merged document as a page: its title and sections, without its frame and phase table."""
    lines = merged.path.read_text(encoding="utf-8-sig").split("\n")
    dropped = {phase.line for phase in merged.document.phases}
    if merged.document.phase_header is not None:
        header = merged.document.phase_header[0]
        dropped |= {header, header + 1}
    start = merged.document.status_line
    while start < len(lines) and (not lines[start].strip() or K_FIELD.match(lines[start])):
        start += 1
    kept = [line for number, line in enumerate(lines, start=1) if number > start and number not in dropped]
    text = "\n".join([lines[0], "", *kept])
    return K_GENERATED_BLOCK.sub("", text).rstrip("\n") + "\n"


def _words(name: str) -> set[str]:
    """Returns the words of a topic name that can say two topics share a subject."""
    return {word for word in K_NAME_WORD.findall(name) if len(word) >= K_SHORT_WORD and word not in K_COMMON_WORDS}
