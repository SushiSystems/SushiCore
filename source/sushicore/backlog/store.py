# store.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Reads and writes the backlog of one repository: `docs/backlog/` and the files in it.

The layout is in `docs/reference/BACKLOG.md`: one Markdown file per area holding two tables,
`ids.toml` for the counters, `backlog.toml` for the areas and the pins, a generated
`README.md`, and `detail/<ID>.md` for an entry whose explanation does not fit its row.
"""

from __future__ import annotations

import datetime
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterator, Union

from ..errors import ConfigError
from ..workspace import read_toml
from .errors import BacklogError, EntryNotFoundError, RowError
from .model import (
    K_ISSUE_PREFIX,
    K_PRIORITIES,
    K_STATES,
    K_WORK_PREFIX,
    IssueEntry,
    WorkEntry,
    id_number,
    join_row,
    split_row,
)

K_FOLDER = Path("docs") / "backlog"
K_INDEX = "README.md"
K_IDS = "ids.toml"
K_CONFIG = "backlog.toml"
K_DETAIL = "detail"
K_WORK_SECTION = "## Remaining work"
K_ISSUE_SECTION = "## Known issues"
K_AREA_NAME = re.compile(r"^[A-Z][A-Z0-9_]*$")
K_CONFLICT_MARK = re.compile(r"^(<{7}|={7}|>{7}|\|{7})(\s.*)?$")
K_PIN_CEILING = 10
K_KIND_TABLES = {K_WORK_PREFIX: "work", K_ISSUE_PREFIX: "issue"}

AnyEntry = Union[WorkEntry, IssueEntry]


@dataclass(frozen=True, slots=True)
class Fault:
    """A line of a backlog file that is not in the shape the tool writes."""

    path: Path
    line: int
    message: str


@dataclass(frozen=True, slots=True)
class Located:
    """An entry with the file and the line it was read from."""

    entry: AnyEntry
    path: Path
    line: int
    area: str


@dataclass(slots=True)
class AreaFile:
    """The entries of one area, both kinds, in the order the file holds them."""

    area: str
    work: list[WorkEntry] = field(default_factory=list)
    issues: list[IssueEntry] = field(default_factory=list)
    lines: dict[str, int] = field(default_factory=dict)

    def entries(self) -> list[AnyEntry]:
        """Returns the work entries, then the issues."""
        return [*self.work, *self.issues]

    def put(self, entry: AnyEntry) -> None:
        """Adds an entry, or replaces the one with its ID, and keeps each table sorted by ID."""
        table = self.work if isinstance(entry, WorkEntry) else self.issues
        kept = [item for item in table if item.ident != entry.ident]
        kept.append(entry)
        kept.sort(key=lambda item: id_number(item.ident))
        table[:] = kept

    def drop(self, ident: str) -> bool:
        """Removes the entry with the ID; returns whether there was one."""
        before = len(self.work) + len(self.issues)
        self.work[:] = [item for item in self.work if item.ident != ident]
        self.issues[:] = [item for item in self.issues if item.ident != ident]
        return len(self.work) + len(self.issues) != before


@dataclass(frozen=True, slots=True)
class BacklogConfig:
    """The areas a repository allows and the owner's pins, from `backlog.toml`."""

    areas: tuple[str, ...]
    pins: tuple[str, ...] = ()


@dataclass(slots=True)
class IdLedger:
    """The next number of each kind and every number ever closed, from `ids.toml`."""

    next: dict[str, int] = field(default_factory=lambda: {K_WORK_PREFIX: 1, K_ISSUE_PREFIX: 1})
    closed: dict[str, set[int]] = field(
        default_factory=lambda: {K_WORK_PREFIX: set(), K_ISSUE_PREFIX: set()})

    def take(self, prefix: str) -> str:
        """Returns the next ID of a kind and moves its counter on."""
        number = self.next[prefix]
        self.next[prefix] = number + 1
        return f"{prefix}-{number}"

    def close(self, ident: str) -> None:
        """Records an ID as closed, so it is never used again."""
        self.closed[ident[:2]].add(id_number(ident))

    def is_closed(self, ident: str) -> bool:
        """Returns whether the ID was closed."""
        return id_number(ident) in self.closed[ident[:2]]


def area_title(area: str) -> str:
    """Returns the heading of an area file: `CLI_TOOLS` becomes `Cli tools`."""
    return area.replace("_", " ").capitalize()


def render_area(area: AreaFile) -> str:
    """Returns the text of an area file, the only shape the tool writes."""
    lines = [f"# {area_title(area.area)}", "", K_WORK_SECTION, ""]
    lines += _table(WorkEntry.COLUMNS, [entry.cells() for entry in area.work])
    lines += ["", K_ISSUE_SECTION, ""]
    lines += _table(IssueEntry.COLUMNS, [entry.cells() for entry in area.issues])
    return "\n".join(lines) + "\n"


def parse_area(
    path: Path, text: str, *, tolerate_conflicts: bool = False,
) -> tuple[AreaFile, list[Fault]]:
    """Returns the entries an area file holds and every line out of the shape the tool writes.

    With *tolerate_conflicts*, the marker lines a merge conflict leaves are dropped and the rows
    of both sides are kept, which is how `renumber` reads a file git could not merge.
    """
    area = AreaFile(path.stem)
    faults: list[Fault] = []
    kind: type[WorkEntry] | type[IssueEntry] | None = None
    header_seen = False
    for number, line in enumerate(text.splitlines(), start=1):
        if tolerate_conflicts and K_CONFLICT_MARK.match(line):
            continue
        if number == 1:
            if line != f"# {area_title(area.area)}":
                faults.append(Fault(path, 1, f"the title is '# {area_title(area.area)}'"))
            continue
        if line in (K_WORK_SECTION, K_ISSUE_SECTION):
            kind = WorkEntry if line == K_WORK_SECTION else IssueEntry
            header_seen = False
            continue
        if not line.strip():
            continue
        if kind is None or not line.startswith("|"):
            faults.append(Fault(path, number, "an area file holds its title, two sections and their tables"))
            continue
        try:
            cells = split_row(line)
        except RowError as error:
            faults.append(Fault(path, number, str(error)))
            continue
        if not header_seen:
            header_seen = True
            if tuple(cells) != kind.COLUMNS:
                faults.append(Fault(path, number, f"the columns are {', '.join(kind.COLUMNS)}"))
            continue
        if all(set(cell) <= {"-", ":"} and cell for cell in cells):
            continue
        try:
            entry = kind.from_cells(cells)
        except RowError as error:
            faults.append(Fault(path, number, str(error)))
            continue
        (area.work if kind is WorkEntry else area.issues).append(entry)
        area.lines[entry.ident] = number
    return area, faults


class BacklogStore:
    """The backlog of one repository, read from and written to `docs/backlog/`."""

    def __init__(self, root: Path, today: Callable[[], datetime.date] = datetime.date.today) -> None:
        """Keeps the repository root and the clock that dates a new entry."""
        self.root = root
        self.folder = root / K_FOLDER
        self.today = today

    def exists(self) -> bool:
        """Returns whether the repository has a backlog folder."""
        return self.folder.is_dir()

    def config(self) -> BacklogConfig:
        """Returns the areas and the pins.

        @throws BacklogError When `backlog.toml` is missing or names no area.
        """
        try:
            table = read_toml(self.folder / K_CONFIG).get("backlog", {})
        except ConfigError as error:
            raise BacklogError(str(error)) from error
        areas = tuple(table.get("areas", ()))
        if not areas:
            raise BacklogError(f"{self.folder / K_CONFIG} names no area under [backlog] areas")
        return BacklogConfig(areas, tuple(table.get("pins", ())))

    def write_config(self, config: BacklogConfig) -> None:
        """Writes `backlog.toml`."""
        text = (
            "[backlog]\n"
            f"areas = {_toml_list(config.areas)}\n"
            f"pins = {_toml_list(config.pins)}\n"
        )
        self._write(self.folder / K_CONFIG, text)

    def ledger(self) -> IdLedger:
        """Returns the counters and the closed IDs.

        @throws BacklogError When `ids.toml` is not valid.
        """
        try:
            data = read_toml(self.folder / K_IDS)
        except ConfigError as error:
            raise BacklogError(str(error)) from error
        ledger = IdLedger()
        for prefix, name in K_KIND_TABLES.items():
            table = data.get(name, {})
            ledger.next[prefix] = int(table.get("next", 1))
            ledger.closed[prefix] = parse_ranges(str(table.get("closed", "")))
        return ledger

    def write_ledger(self, ledger: IdLedger) -> None:
        """Writes `ids.toml`, one line per value, so two branches conflict on one line."""
        parts = []
        for prefix, name in K_KIND_TABLES.items():
            parts.append(
                f"[{name}]\nnext = {ledger.next[prefix]}\n"
                f"closed = \"{format_ranges(ledger.closed[prefix])}\"\n"
            )
        self._write(self.folder / K_IDS, "\n".join(parts))

    def area_path(self, area: str) -> Path:
        """Returns the file of an area."""
        return self.folder / f"{area}.md"

    def read_area(self, area: str) -> AreaFile:
        """Returns the entries of an area; an area with no file yet is empty.

        @throws BacklogError When the file is not in the shape the tool writes.
        """
        path = self.area_path(area)
        if not path.is_file():
            return AreaFile(area)
        parsed, faults = parse_area(path, path.read_text(encoding="utf-8"))
        if faults:
            first = faults[0]
            raise BacklogError(f"{first.path}:{first.line}: {first.message}; run `backlog check`")
        return parsed

    def write_area(self, area: AreaFile) -> None:
        """Writes an area file."""
        self._write(self.area_path(area.area), render_area(area))

    def located(self) -> Iterator[Located]:
        """Yields every entry of every configured area, with where it was read."""
        for area in self.config().areas:
            parsed = self.read_area(area)
            for entry in parsed.entries():
                yield Located(entry, self.area_path(area), parsed.lines.get(entry.ident, 1), area)

    def entries(self) -> list[AnyEntry]:
        """Returns every entry of every configured area."""
        return [item.entry for item in self.located()]

    def find(self, ident: str) -> Located:
        """Returns the entry with the ID.

        @throws EntryNotFoundError When no open entry has it.
        """
        for item in self.located():
            if item.entry.ident == ident:
                return item
        raise EntryNotFoundError(f"{ident} names no open entry")

    def detail_path(self, ident: str) -> Path:
        """Returns the file that holds the longer explanation of an entry."""
        return self.folder / K_DETAIL / f"{ident}.md"

    def write_detail(self, ident: str, text: str) -> Path:
        """Writes the detail file of an entry and returns its path."""
        path = self.detail_path(ident)
        self._write(path, text)
        return path

    def relative(self, path: Path) -> str:
        """Returns a path from the repository root, as a Source cell writes it."""
        return path.relative_to(self.root).as_posix()

    def write_index(self) -> None:
        """Writes the generated `README.md`."""
        self._write(self.folder / K_INDEX, self.render_index())

    def render_index(self) -> str:
        """Returns the text of the generated `README.md`: each area, counted by state and priority."""
        config = self.config()
        lines = [
            "# Backlog",
            "",
            "Generated by the `backlog` commands; every change goes through them. "
            "`backlog next` gives the order, `backlog list --late` the entries past their age limit.",
            "",
            "| Area | Work | Issues | " + " | ".join(K_STATES) + " | " + " | ".join(K_PRIORITIES) + " |",
            "| --- | --- | --- | " + " | ".join("---" for _ in (*K_STATES, *K_PRIORITIES)) + " |",
        ]
        for area in config.areas:
            parsed = self.read_area(area)
            states = [str(sum(1 for item in parsed.work if item.state == state)) for state in K_STATES]
            priorities = [
                str(sum(1 for item in parsed.work if item.priority == priority))
                for priority in K_PRIORITIES
            ]
            lines.append(
                f"| [{area_title(area)}]({area}.md) | {len(parsed.work)} | {len(parsed.issues)} | "
                + " | ".join(states) + " | " + " | ".join(priorities) + " |"
            )
        if config.pins:
            lines += ["", "Pinned by the owner: " + ", ".join(config.pins) + "."]
        return "\n".join(lines) + "\n"

    def _write(self, path: Path, text: str) -> None:
        """Writes a file of the store with LF line ends."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")


def parse_ranges(text: str) -> set[int]:
    """Returns the numbers a list such as `1-4,7` names.

    @throws BacklogError When an item is not a number or a range.
    """
    found: set[int] = set()
    for item in (part.strip() for part in text.split(",")):
        if not item:
            continue
        low, _, high = item.partition("-")
        try:
            found.update(range(int(low), int(high or low) + 1))
        except ValueError as error:
            raise BacklogError(f"ids.toml: '{item}' is not a number or a range") from error
    return found


def format_ranges(numbers: set[int]) -> str:
    """Returns the shortest list of numbers and ranges, such as `1-4,7`."""
    parts: list[str] = []
    ordered = sorted(numbers)
    index = 0
    while index < len(ordered):
        start = index
        while index + 1 < len(ordered) and ordered[index + 1] == ordered[index] + 1:
            index += 1
        low, high = ordered[start], ordered[index]
        parts.append(str(low) if low == high else f"{low}-{high}")
        index += 1
    return ",".join(parts)


def is_area_name(name: str) -> bool:
    """Returns whether a name can be an area: upper case words joined by underscores."""
    return bool(K_AREA_NAME.match(name))


def _table(columns: tuple[str, ...], rows: list[list[str]]) -> list[str]:
    """Returns the lines of a table: the header, the rule and one line per row."""
    return [join_row(list(columns)), join_row(["---"] * len(columns)), *(join_row(row) for row in rows)]


def _toml_list(items: tuple[str, ...]) -> str:
    """Returns a TOML array of strings."""
    return "[" + ", ".join(f"\"{item}\"" for item in items) + "]"
