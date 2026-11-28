# history.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Reads from git when each entry opened and closed, and which paths each commit changed.

`flow.py` and `triage.py` judge what this reads.
"""

from __future__ import annotations

import datetime
import re
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import final

from .admission import covers
from .model import K_ID, split_row
from .store import K_FOLDER
from .verification import run_git

K_RECORD = "\x1e"
K_DATED_FORMAT = f"--format={K_RECORD}%ad"
K_ROW = re.compile(r"^(?P<sign>[+-])(?P<row>\|.*\|)\s*$")


@final
@dataclass(slots=True)
class EntryLife:
    """Holds one entry as git saw it: its ID, the day it opened, the day it closed, and its Source."""

    ident: str
    opened: datetime.date
    source: str
    closed: datetime.date | None = None

    @property
    def is_work(self) -> bool:
        """Returns whether the entry is remaining work rather than a known issue."""
        return self.ident.startswith("RW-")


@final
@dataclass(frozen=True, slots=True)
class PathChange:
    """Holds one commit's date and the paths it changed."""

    date: datetime.date
    paths: tuple[str, ...]


@final
@dataclass(frozen=True, slots=True)
class Recorded:
    """Holds what git recorded of a backlog: each entry's life and each commit's paths, oldest first."""

    lives: list[EntryLife] = field(default_factory=list)
    changes: list[PathChange] = field(default_factory=list)


def parse_backlog_log(log: str) -> list[EntryLife]:
    """Returns each entry's life from `git log --reverse -p --unified=0` of the backlog folder.

    The log uses the format `K_DATED_FORMAT` with `--date=short`. A row removed and written again
    in one commit was edited or moved, so it stays open; a row removed alone was closed.
    """
    lives: dict[str, EntryLife] = {}
    for record in log.split(K_RECORD)[1:]:
        date_text, _, body = record.partition("\n")
        date = datetime.date.fromisoformat(date_text.strip())
        added: dict[str, str] = {}
        removed: set[str] = set()
        for line in body.splitlines():
            match = K_ROW.match(line)
            if match is None:
                continue
            cells = split_row(match["row"])
            if not cells or K_ID.match(cells[0]) is None:
                continue
            if match["sign"] == "+":
                added[cells[0]] = cells[-2]
            else:
                removed.add(cells[0])
        for ident, source in added.items():
            known = lives.get(ident)
            if known is None or known.closed is not None:
                lives[ident] = EntryLife(ident, date, source)
            else:
                known.source = source
        for ident in removed - added.keys():
            if ident in lives and lives[ident].closed is None:
                lives[ident].closed = date
    return list(lives.values())


def parse_path_log(log: str) -> list[PathChange]:
    """Returns each commit's date and paths from `git log --name-only` in the format `K_DATED_FORMAT`."""
    changes = []
    for record in log.split(K_RECORD)[1:]:
        date_text, _, listing = record.partition("\n")
        paths = tuple(line.strip() for line in listing.splitlines() if line.strip())
        changes.append(PathChange(datetime.date.fromisoformat(date_text.strip()), paths))
    return changes


def changes_after(source: str, day: datetime.date, changes: Iterable[PathChange]) -> int:
    """Returns how many commits after *day* changed a path the `Source` cell covers."""
    return sum(
        1 for change in changes
        if change.date > day and any(covers(source, path) for path in change.paths))


@final
class GitHistory:
    """Reads a checkout's backlog history and its changed paths from git."""

    def __init__(self, git: Callable[..., str | None] = run_git) -> None:
        """Takes the function that runs git, so a test can replace it."""
        self._git = git

    def read(self, root: Path) -> Recorded | None:
        """Returns what git recorded of the backlog at *root*, or None when git cannot read it."""
        folder = K_FOLDER.as_posix()
        backlog = self._git(
            root, "log", "--reverse", "-p", "--unified=0", "--no-renames", K_DATED_FORMAT,
            "--date=short", "--", folder)
        if backlog is None:
            return None
        lives = parse_backlog_log(backlog)
        if not lives:
            return Recorded()
        since = min(life.opened for life in lives).isoformat()
        paths = self._git(
            root, "log", "--reverse", "--name-only", "--no-renames", K_DATED_FORMAT, "--date=short",
            f"--since={since}")
        if paths is None:
            return None
        return Recorded(lives, parse_path_log(paths))
