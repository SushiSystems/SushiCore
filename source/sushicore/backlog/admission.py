# admission.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Judges a commit being made against the backlog: the entries it changes and the entries it opens.

The rules are in `docs/reference/BACKLOG.md`, section "A commit and the backlog".
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import final

from .model import WorkEntry, source_path
from .store import AnyEntry

K_REMAINDER_CEILING = 3
K_DOCS_PREFIX = "docs/"


@final
@dataclass(frozen=True, slots=True)
class StagedChange:
    """Holds a commit being made: its changed paths, the entries open at its parent, the IDs it names."""

    paths: tuple[str, ...]
    parent_ids: frozenset[str]
    named: frozenset[str]


def covers(source: str, path: str) -> bool:
    """Returns whether a `Source` cell names *path* or a folder that holds it."""
    named = source_path(source)
    if not named:
        return False
    folder = named.rstrip("/")
    return path == folder or path.startswith(folder + "/")


def entries_on(entries: Iterable[AnyEntry], paths: Iterable[str]) -> list[AnyEntry]:
    """Returns each entry whose `Source` covers one of *paths*, in the order given."""
    wanted = list(paths)
    return [entry for entry in entries if any(covers(entry.source, path) for path in wanted)]


def admission_problems(
    entries: Iterable[AnyEntry], change: StagedChange, ceiling: int = K_REMAINDER_CEILING,
) -> list[str]:
    """Returns why the backlog refuses a commit; empty when it accepts it.

    *entries* are the entries open once the commit is made. A path under `docs/` is a citation,
    not a place of work, so neither rule reads it.
    """
    places = [path for path in change.paths if not path.startswith(K_DOCS_PREFIX)]
    work = [entry for entry in entries_on(entries, places) if isinstance(entry, WorkEntry)]
    left = [entry for entry in work if entry.ident in change.parent_ids and entry.ident not in change.named]
    opened = [entry for entry in work if entry.ident not in change.parent_ids]
    problems: list[str] = []
    if left:
        problems.append(
            "this commit changes the Source of " + _listed(left)
            + "; close each one it finishes with `backlog close`, and name the rest in the `Backlog:` line")
    if len(opened) > ceiling:
        problems.append(
            f"this commit opens {len(opened)} entries on files it changes, " + _listed(opened)
            + f"; at most {ceiling}: finish that work here, or keep it in the one entry of its work folder")
    return problems


def _listed(entries: list[WorkEntry]) -> str:
    """Returns the entries as `RW-1 (title), RW-2 (title)`."""
    return ", ".join(f"{entry.ident} ({entry.title})" for entry in entries)
