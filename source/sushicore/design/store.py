# store.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Reads and writes the design topics of one repository and answers which topic owns a module.

A topic is the folder `docs/design/<TOPIC>/`, whose `README.md` is its document; a topic under
revision sits in `docs/design/_REVISION/<TOPIC>/`.
"""

from __future__ import annotations

import datetime
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from .errors import DesignError, OwnedModuleError, TopicNotFoundError
from .model import (
    K_CLOSED_PHASE_STATES,
    K_MODULES_FIELD,
    K_PHASE_ID,
    K_PHASE_STATES,
    Phase,
    TopicDocument,
    is_topic_name,
    open_status,
    parse_topic,
    render_topic,
    replace_field,
    replace_phases,
    replace_status,
    shipped_status,
)

K_DESIGN = Path("docs") / "design"
K_AGENT = Path("docs") / "agent"
K_README = "README.md"
K_REVISION = "_REVISION"
K_INDEXES = frozenset({"README.md", "REMAINING_WORK.md"})
K_WORK_FILES_IN_ORDER = ("SPEC.md", "PLAN.md", "REPORT.md")


@dataclass(frozen=True, slots=True)
class Topic:
    """One topic: its name, its document and the frame read from it."""

    name: str
    path: Path
    document: TopicDocument

    def is_under_revision(self) -> bool:
        """Returns whether the topic waits in _REVISION."""
        return K_REVISION in self.path.parts


class DesignStore:
    """The design topics of one repository."""

    def __init__(self, root: Path, today: Callable[[], datetime.date] = datetime.date.today) -> None:
        """Keeps the repository root and the clock a status line is dated with."""
        self.root = root
        self.design = root / K_DESIGN
        self.today = today

    def documents(self) -> list[Path]:
        """Returns every topic document, a loose one in docs/design and those under revision included."""
        if not self.design.is_dir():
            return []
        revision = self.design / K_REVISION
        found = [path for path in sorted(self.design.glob("*.md")) if path.name not in K_INDEXES]
        found += [
            folder / K_README for folder in sorted(self.design.iterdir())
            if folder.is_dir() and folder != revision
        ]
        if revision.is_dir():
            found += [folder / K_README for folder in sorted(revision.iterdir()) if folder.is_dir()]
        return found

    def loose_documents(self) -> list[Path]:
        """Returns each document that sits directly in docs/design and is not an index."""
        return [path for path in self.documents() if path.parent == self.design]

    def topic_paths(self) -> dict[str, Path]:
        """Returns the document of each topic by name."""
        return {
            path.parent.name if path.name == K_README else path.stem: path
            for path in self.documents() if path.is_file()
        }

    def topics(self) -> list[Topic]:
        """Returns every topic with its frame."""
        return [
            Topic(name, path, parse_topic(path.read_text(encoding="utf-8-sig")))
            for name, path in self.topic_paths().items()
        ]

    def topic(self, name: str) -> Topic:
        """Returns one topic.

        @throws TopicNotFoundError When no topic has the name.
        """
        path = self.topic_paths().get(name)
        if path is None:
            raise TopicNotFoundError(f"'{name}' is not a design topic")
        return Topic(name, path, parse_topic(path.read_text(encoding="utf-8-sig")))

    def open_documents(self) -> list[Path]:
        """Returns the document of each topic whose status is Open, those under revision left out."""
        return [topic.path for topic in self.topics() if topic.document.is_open() and not topic.is_under_revision()]

    def owners(self) -> dict[str, list[str]]:
        """Returns each module path a topic names, with every topic that names it.

        A topic under revision is frozen until it is rewritten, so it owns nothing.
        """
        found: dict[str, list[str]] = {}
        for topic in self.topics():
            if topic.is_under_revision():
                continue
            for module in topic.document.modules() or []:
                found.setdefault(_normal(module), []).append(topic.name)
        return found

    def owner(self, path: str) -> str | None:
        """Returns the topic that owns the module holding *path*, the deepest named module first."""
        target = PurePosixPath(_normal(path))
        best: tuple[int, str] | None = None
        for module, names in self.owners().items():
            candidate = PurePosixPath(module)
            if target == candidate or candidate in target.parents:
                depth = len(candidate.parts)
                if best is None or depth > best[0]:
                    best = (depth, names[0])
        return None if best is None else best[1]

    def claimed(self, modules: list[str]) -> list[tuple[str, str, str]]:
        """Returns each module of *modules* that lies in, holds or is a module a topic names.

        Each item is the asked module, the module named and the topic naming it.
        """
        found: list[tuple[str, str, str]] = []
        for asked in modules:
            mine = PurePosixPath(_normal(asked))
            for module, names in self.owners().items():
                theirs = PurePosixPath(module)
                if mine == theirs or theirs in mine.parents or mine in theirs.parents:
                    found += [(asked, module, name) for name in names]
        return found

    def create(self, name: str, *, modules: list[str], about: str) -> Path:
        """Writes a new topic and returns its document.

        @throws DesignError When the name is not a topic name or is taken, a module does not
            exist, or *about* is empty.
        @throws OwnedModuleError When another topic owns a module, or one inside or around it.
        """
        if not is_topic_name(name):
            raise DesignError(f"'{name}' is not a topic name: upper case words joined by _")
        if name in self.topic_paths():
            raise DesignError(f"the topic {name} exists; add a page or a phase to it")
        if not about.strip():
            raise DesignError("--about says in one sentence what the topic is")
        for module in modules:
            if not (self.root / module).exists():
                raise DesignError(f"the module '{module}' is not in the repository")
        claimed = self.claimed(modules)
        if claimed:
            asked, module, owner = claimed[0]
            raise OwnedModuleError(
                f"'{asked}' is owned by {owner}, which names '{module}'; "
                f"add a page to {owner} with `design page {owner} <PAGE>`"
            )
        path = self.design / name / K_README
        title = name.replace("_", " ").capitalize()
        self.write_file(path, render_topic(title, about.strip(), [_normal(m) for m in modules], []))
        return path

    def add_page(self, name: str, page: str) -> Path:
        """Writes an empty page beside a topic's README.md and returns it.

        @throws DesignError When the topic is a loose file, or the page exists.
        """
        topic = self.topic(name)
        if topic.path.name != K_README:
            raise DesignError(f"{name} is a loose file; give it its folder first")
        stem = page.removesuffix(".md").upper()
        if not is_topic_name(stem):
            raise DesignError(f"'{page}' is not a page name: upper case words joined by _")
        path = topic.path.parent / f"{stem}.md"
        if path.exists():
            raise DesignError(f"{path} exists")
        self.write_file(path, f"# {stem.replace('_', ' ').capitalize()}\n")
        return path

    def add_phase(self, name: str, ident: str, text: str) -> Phase:
        """Adds a planned phase to a topic and reopens it when it had shipped.

        @throws DesignError When the id is taken or out of shape.
        """
        topic = self.topic(name)
        if not K_PHASE_ID.match(ident):
            raise DesignError(f"'{ident}' is not a phase id: a letter, then letters, digits, . _ or -")
        if any(phase.ident == ident for phase in topic.document.phases):
            raise DesignError(f"{name} has a phase {ident}")
        phase = Phase(ident, " ".join(text.split()), "planned")
        self._write_phases(topic, [*topic.document.phases, phase])
        return phase

    def set_phase_state(self, name: str, ident: str, state: str) -> str:
        """Moves a phase to a state and returns the topic's status line after it.

        @throws DesignError When the state is unknown or the topic has no such phase.
        """
        if state not in K_PHASE_STATES:
            raise DesignError(f"a phase state is one of {', '.join(K_PHASE_STATES)}")
        topic = self.topic(name)
        phases = topic.document.phases
        if not any(phase.ident == ident for phase in phases):
            raise DesignError(f"{name} has no phase {ident}")
        changed = [Phase(p.ident, p.text, state) if p.ident == ident else p for p in phases]
        return self._write_phases(topic, changed)

    def set_modules(self, name: str, modules: list[str]) -> None:
        """Rewrites a topic's Modules line."""
        topic = self.topic(name)
        value = ", ".join(f"`{_normal(m)}`" for m in modules) if modules else "none"
        text = topic.path.read_text(encoding="utf-8-sig")
        self.write_file(topic.path, replace_field(text, K_MODULES_FIELD, value))

    def relative(self, path: Path) -> str:
        """Returns a path from the repository root."""
        return path.relative_to(self.root).as_posix()

    def work_documents(self) -> list[Path]:
        """Returns the first file of each work folder, the one that carries its metadata."""
        agent = self.root / K_AGENT
        found: list[Path] = []
        for folder in sorted(agent.iterdir()) if agent.is_dir() else []:
            first = next((folder / n for n in K_WORK_FILES_IN_ORDER if (folder / n).is_file()), None)
            if first is not None:
                found.append(first)
        return found

    def _write_phases(self, topic: Topic, phases: list[Phase]) -> str:
        """Writes a topic's phase table and the status it implies; returns the status."""
        text = replace_phases(topic.path.read_text(encoding="utf-8-sig"), phases)
        is_closed = bool(phases) and all(phase.state in K_CLOSED_PHASE_STATES for phase in phases)
        status = topic.document.status.removeprefix("**Status:** ")
        if is_closed:
            status = shipped_status(self.today())
        elif not topic.document.is_open():
            status = open_status(phases)
        self.write_file(topic.path, replace_status(text, status))
        return status

    def write_file(self, path: Path, text: str) -> None:
        """Writes a design file with LF line ends."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")


def _normal(path: str) -> str:
    """Returns a module path from the root with forward slashes and no trailing slash."""
    return path.strip().strip("`").replace("\\", "/").rstrip("/").removeprefix("./")
