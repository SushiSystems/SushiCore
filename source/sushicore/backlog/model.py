# model.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""The two kinds of backlog entry, their columns and values, and one table row read or written.

The rules are in `docs/reference/BACKLOG.md`.
"""

from __future__ import annotations

import datetime
import re
from dataclasses import dataclass, replace
from typing import ClassVar, Protocol

from .errors import RowError

K_WORK_PREFIX = "RW"
K_ISSUE_PREFIX = "KI"
K_PRIORITIES = ("P0", "P1", "P2", "P3")
K_STATES = ("decision", "open", "blocked", "unmeasured")
K_ORIGINS = ("own", "toolchain", "dependency")
K_TITLE_CEILING = 90
K_DONE_WHEN_CEILING = 160
K_CELL_CEILING = 160
K_NONE = "none"
K_ID = re.compile(r"^(?P<prefix>RW|KI)-(?P<number>[1-9]\d*)$")
K_REFERENCE = re.compile(r"^(?:(?P<owner>[a-z0-9][a-z0-9_.-]*) )?(?P<id>(?:RW|KI)-[1-9]\d*)$")
K_EXTERNAL = re.compile(r"^external: \S")
K_FIX = re.compile(r"^(?:RW-[1-9]\d*|none, \S.*)$")
K_SOURCE = re.compile(r"^`(?P<path>[^`]+)`(?: §\d+(?:\.\d+)*)?$")
K_SIBLING_ORIGIN = re.compile(r"^(?P<owner>[a-z0-9][a-z0-9_.-]*) (?P<id>KI-[1-9]\d*)$")
K_ESCAPED_PIPE = "\\|"
K_SPLIT = re.compile(r"(?<!\\)\|")


def split_row(line: str) -> list[str]:
    """Returns the cells of a table row, unescaped and trimmed.

    @throws RowError When the line is not a table row.
    """
    text = line.strip()
    if not (text.startswith("|") and text.endswith("|")) or len(text) < 2:
        raise RowError(f"not a table row: {line!r}")
    return [cell.strip().replace(K_ESCAPED_PIPE, "|") for cell in K_SPLIT.split(text[1:-1])]


def join_row(cells: list[str]) -> str:
    """Returns the table row that holds *cells*, with each pipe inside a cell escaped."""
    escaped = [cell.replace("|", K_ESCAPED_PIPE) for cell in cells]
    return "| " + " | ".join(escaped) + " |"


def split_references(value: str) -> list[str]:
    """Returns the items of a list cell such as `Blocked by`, separated by commas."""
    if K_EXTERNAL.match(value):
        return [value]
    return [item.strip() for item in value.split(",") if item.strip()]


def id_number(ident: str) -> int:
    """Returns the number of an ID such as RW-12.

    @throws RowError When the text is not an ID.
    """
    match = K_ID.match(ident)
    if match is None:
        raise RowError(f"'{ident}' is not an ID of the form RW-<n> or KI-<n>")
    return int(match["number"])


def source_path(source: str) -> str | None:
    """Returns the path a `Source` cell names, or None when the cell is empty or out of shape."""
    match = K_SOURCE.match(source)
    return None if match is None else match["path"]


class Entry(Protocol):
    """What the store, the order and the check read from an entry of either kind."""

    ident: str
    opened: datetime.date
    source: str

    @property
    def prefix(self) -> str:
        """Returns RW or KI."""

    def cells(self) -> list[str]:
        """Returns the row's cells in column order."""

    def problems(self) -> list[str]:
        """Returns each value of the entry that breaks a rule of its kind."""

    def cited(self) -> list[str]:
        """Returns each entry ID this entry cites."""


@dataclass(frozen=True, slots=True)
class WorkEntry:
    """One remaining work entry: what is to be done, when it is done, and its place in the order."""

    COLUMNS: ClassVar[tuple[str, ...]] = (
        "ID", "Pri", "State", "Title", "Done when", "Blocked by", "Source", "Opened",
    )
    EDITABLE: ClassVar[dict[str, str]] = {
        "Pri": "priority", "State": "state", "Title": "title", "Done when": "done_when",
        "Blocked by": "blocked_by", "Source": "source",
    }

    ident: str
    priority: str
    state: str
    title: str
    done_when: str
    blocked_by: str
    source: str
    opened: datetime.date

    @property
    def prefix(self) -> str:
        """Returns RW."""
        return K_WORK_PREFIX

    @classmethod
    def from_cells(cls, cells: list[str]) -> WorkEntry:
        """Returns the entry a row holds.

        @throws RowError When the row has the wrong number of cells or an unreadable date.
        """
        values = _checked_cells(cls.COLUMNS, cells)
        return cls(*values[:-1], _date(values[-1]))

    def cells(self) -> list[str]:
        """Returns the row's cells in column order."""
        return [
            self.ident, self.priority, self.state, self.title, self.done_when, self.blocked_by,
            self.source, self.opened.isoformat(),
        ]

    def with_value(self, column: str, value: str) -> WorkEntry:
        """Returns a copy with one editable column changed.

        @throws RowError When the column is not one a caller may set.
        """
        return replace(self, **{_editable(self.EDITABLE, column): value})

    def blocks(self) -> list[str]:
        """Returns the IDs this entry waits on, without external reasons."""
        return [item for item in split_references(self.blocked_by) if K_REFERENCE.match(item)]

    def cited(self) -> list[str]:
        """Returns each entry ID this entry cites."""
        return self.blocks()

    def problems(self) -> list[str]:
        """Returns each value of the entry that breaks a rule of remaining work."""
        found = _common_problems(self.ident, K_WORK_PREFIX, self.source)
        if self.priority not in K_PRIORITIES:
            found.append(f"Pri is one of {', '.join(K_PRIORITIES)}")
        if self.state not in K_STATES:
            found.append(f"State is one of {', '.join(K_STATES)}")
        found += _length("Title", self.title, K_TITLE_CEILING)
        found += _length("Done when", self.done_when, K_DONE_WHEN_CEILING)
        if (self.state == "blocked") != bool(self.blocked_by):
            found.append("Blocked by is filled when State is blocked, and only then")
        for item in split_references(self.blocked_by):
            if not (K_REFERENCE.match(item) or K_EXTERNAL.match(item)):
                found.append(f"Blocked by: '{item}' is not an ID or 'external: <reason>'")
        return found


@dataclass(frozen=True, slots=True)
class IssueEntry:
    """One known issue: a condition a reader can meet, where it comes from and how to work around it."""

    COLUMNS: ClassVar[tuple[str, ...]] = (
        "ID", "Origin", "Symptom", "Workaround", "Fix", "Source", "Opened",
    )
    EDITABLE: ClassVar[dict[str, str]] = {
        "Origin": "origin", "Symptom": "symptom", "Workaround": "workaround", "Fix": "fix",
        "Source": "source",
    }

    ident: str
    origin: str
    symptom: str
    workaround: str
    fix: str
    source: str
    opened: datetime.date

    @property
    def prefix(self) -> str:
        """Returns KI."""
        return K_ISSUE_PREFIX

    @classmethod
    def from_cells(cls, cells: list[str]) -> IssueEntry:
        """Returns the entry a row holds.

        @throws RowError When the row has the wrong number of cells or an unreadable date.
        """
        values = _checked_cells(cls.COLUMNS, cells)
        return cls(*values[:-1], _date(values[-1]))

    def cells(self) -> list[str]:
        """Returns the row's cells in column order."""
        return [
            self.ident, self.origin, self.symptom, self.workaround, self.fix, self.source,
            self.opened.isoformat(),
        ]

    def with_value(self, column: str, value: str) -> IssueEntry:
        """Returns a copy with one editable column changed.

        @throws RowError When the column is not one a caller may set.
        """
        return replace(self, **{_editable(self.EDITABLE, column): value})

    def is_own(self) -> bool:
        """Returns whether the repository itself is where the issue comes from."""
        return self.origin == "own"

    def cited(self) -> list[str]:
        """Returns the work entry that fixes this issue and the sibling's issue it comes from."""
        found = [self.fix] if K_REFERENCE.match(self.fix) else []
        return found + ([self.origin] if K_SIBLING_ORIGIN.match(self.origin) else [])

    def problems(self) -> list[str]:
        """Returns each value of the entry that breaks a rule of known issues."""
        found = _common_problems(self.ident, K_ISSUE_PREFIX, self.source)
        if self.origin not in K_ORIGINS and not K_SIBLING_ORIGIN.match(self.origin):
            found.append("Origin is own, toolchain, dependency or '<repository> KI-<n>'")
        found += _length("Symptom", self.symptom, K_TITLE_CEILING)
        found += _length("Workaround", self.workaround, K_CELL_CEILING)
        if not self.workaround:
            found.append(f"Workaround is text, or '{K_NONE}'")
        if self.fix and not K_FIX.match(self.fix):
            found.append("Fix is 'RW-<n>' or 'none, <reason>'")
        if len(self.fix) > K_CELL_CEILING:
            found.append(f"Fix is {len(self.fix)} characters; the ceiling is {K_CELL_CEILING}")
        if self.is_own() and not self.fix:
            found.append("Fix is required when the origin is own")
        if self.is_own() and self.fix.startswith("RW-") and self.workaround == K_NONE:
            found.append(f"a scheduled fix and no workaround is remaining work alone: {self.fix}")
        return found


K_KINDS: dict[str, type[WorkEntry] | type[IssueEntry]] = {
    K_WORK_PREFIX: WorkEntry,
    K_ISSUE_PREFIX: IssueEntry,
}


def column_names(prefix: str) -> tuple[str, ...]:
    """Returns the columns of the kind an ID prefix names."""
    return K_KINDS[prefix].COLUMNS


def _checked_cells(columns: tuple[str, ...], cells: list[str]) -> list[str]:
    """Returns the cells when there is one per column."""
    if len(cells) != len(columns):
        raise RowError(f"a row has {len(columns)} cells, {', '.join(columns)}; found {len(cells)}")
    return cells


def _date(text: str) -> datetime.date:
    """Returns the ISO date a cell holds."""
    try:
        return datetime.date.fromisoformat(text)
    except ValueError as error:
        raise RowError(f"Opened is an ISO date; found '{text}'") from error


def _editable(columns: dict[str, str], column: str) -> str:
    """Returns the field behind an editable column."""
    if column not in columns:
        raise RowError(f"'{column}' cannot be set; the columns are {', '.join(columns)}")
    return columns[column]


def _common_problems(ident: str, prefix: str, source: str) -> list[str]:
    """Returns the problems of the ID and the source that both kinds share."""
    found: list[str] = []
    match = K_ID.match(ident)
    if match is None or match["prefix"] != prefix:
        found.append(f"ID is {prefix}-<n>")
    if source and source_path(source) is None:
        found.append("Source is one path in backticks, then an optional '§<n>'")
    return found


def _length(column: str, value: str, ceiling: int) -> list[str]:
    """Returns a problem when a cell is empty or longer than its ceiling."""
    if not value:
        return [f"{column} is required"]
    if len(value) > ceiling:
        return [f"{column} is {len(value)} characters; the ceiling is {ceiling}"]
    return []

