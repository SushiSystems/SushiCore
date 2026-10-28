# editor.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Every change the backlog commands make: add, promote, set, move, close, pin, and the areas.

Each change reads the store, refuses a result that would break a rule of the entry's kind, and
writes the files it touched and the index.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from .errors import EntryNotFoundError, RefusedChangeError
from .model import K_ISSUE_PREFIX, K_WORK_PREFIX, IssueEntry, WorkEntry
from .store import K_PIN_CEILING, AnyEntry, AreaFile, BacklogConfig, BacklogStore, is_area_name


@dataclass(frozen=True, slots=True)
class Closed:
    """What closing an entry did: the entry it deleted and the changelog line to write."""

    entry: AnyEntry
    area: str
    changelog_line: str


class BacklogEditor:
    """Makes the changes of the backlog commands on one store."""

    def __init__(self, store: BacklogStore) -> None:
        """Keeps the store the changes are made on."""
        self.store = store

    def add_work(
        self, *, area: str, priority: str, title: str, done_when: str, source: str = "",
        blocked_by: str = "", state: str | None = None,
    ) -> WorkEntry:
        """Adds a work entry and returns it with its new ID.

        @throws RefusedChangeError When a value breaks a rule or the area is unknown.
        """
        chosen = state or ("blocked" if blocked_by else "open")
        return self._add(area, K_WORK_PREFIX, lambda ident: WorkEntry(
            ident, priority, chosen, title, done_when, blocked_by, _source(source), self.store.today(),
        ))

    def add_issue(
        self, *, area: str, origin: str, symptom: str, workaround: str, fix: str = "",
        source: str = "",
    ) -> IssueEntry:
        """Adds a known issue and returns it with its new ID.

        @throws RefusedChangeError When a value breaks a rule or the area is unknown.
        """
        return self._add(area, K_ISSUE_PREFIX, lambda ident: IssueEntry(
            ident, origin, symptom, workaround, fix, _source(source), self.store.today(),
        ))

    def promote(self, ident: str, *, priority: str, title: str, done_when: str) -> WorkEntry:
        """Opens a work entry from a known issue and writes its ID into the issue's Fix.

        @throws RefusedChangeError When the ID is not an issue, or a value breaks a rule.
        """
        located = self.store.find(ident)
        issue = located.entry
        if not isinstance(issue, IssueEntry):
            raise RefusedChangeError(f"{ident} is not a known issue")
        work = self.add_work(
            area=located.area, priority=priority, title=title, done_when=done_when,
            source=issue.source,
        )
        area = self.store.read_area(located.area)
        area.put(issue.with_value("Fix", work.ident))
        self._save(area)
        return work

    def set_value(self, ident: str, column: str, value: str) -> AnyEntry:
        """Changes one column of an entry and returns it.

        @throws RefusedChangeError When the new value breaks a rule.
        """
        located = self.store.find(ident)
        changed = located.entry.with_value(column, _source(value) if column == "Source" else value)
        _refuse_problems(changed)
        area = self.store.read_area(located.area)
        area.put(changed)
        self._save(area)
        return changed

    def close(self, ident: str, *, commit: str) -> Closed:
        """Deletes an entry and its detail, records the ID as closed and returns its changelog line.

        @throws RefusedChangeError When another open entry cites the ID.
        """
        located = self.store.find(ident)
        citing = [entry.ident for entry in self.store.entries() if ident in entry.cited()]
        if citing:
            raise RefusedChangeError(f"{ident} is cited by {', '.join(citing)}; change those first")
        area = self.store.read_area(located.area)
        area.drop(ident)
        ledger = self.store.ledger()
        ledger.close(ident)
        self.store.write_ledger(ledger)
        detail = self.store.detail_path(ident)
        if detail.is_file():
            detail.unlink()
        config = self.store.config()
        if ident in config.pins:
            self.store.write_config(BacklogConfig(config.areas, tuple(p for p in config.pins if p != ident)))
        self._save(area)
        entry = located.entry
        title = entry.title if isinstance(entry, WorkEntry) else entry.symptom
        line = f"- {self.store.today().isoformat()} — {located.area.lower()}: {title} ({ident}, `{commit}`)."
        return Closed(entry, located.area, line)

    def pin(self, ident: str, position: int | None = None) -> tuple[str, ...]:
        """Puts a work entry in the owner's pins, at a position or last, and returns the pins.

        @throws RefusedChangeError When the entry is not work, is a decision, or the pins are full.
        """
        entry = self.store.find(ident).entry
        if not isinstance(entry, WorkEntry) or entry.state == "decision":
            raise RefusedChangeError(f"{ident} is not work an agent can take")
        config = self.store.config()
        pins = [pin for pin in config.pins if pin != ident]
        if len(pins) >= K_PIN_CEILING:
            raise RefusedChangeError(f"the pins are full at {K_PIN_CEILING}; unpin one first")
        pins.insert(len(pins) if position is None else max(position - 1, 0), ident)
        return self._write_pins(config, tuple(pins))

    def unpin(self, ident: str) -> tuple[str, ...]:
        """Takes an ID out of the pins and returns the pins.

        @throws EntryNotFoundError When the ID is not pinned.
        """
        config = self.store.config()
        if ident not in config.pins:
            raise EntryNotFoundError(f"{ident} is not pinned")
        return self._write_pins(config, tuple(pin for pin in config.pins if pin != ident))

    def add_area(self, area: str) -> tuple[str, ...]:
        """Adds an area to the configuration, writes its empty file and returns the areas.

        @throws RefusedChangeError When the name is not an area name or is taken.
        """
        if not is_area_name(area):
            raise RefusedChangeError(f"'{area}' is not an area name: upper case words joined by _")
        config = self.store.config() if (self.store.folder / "backlog.toml").is_file() else BacklogConfig(())
        if area in config.areas:
            raise RefusedChangeError(f"the area {area} exists")
        areas = tuple(sorted((*config.areas, area)))
        self.store.write_config(BacklogConfig(areas, config.pins))
        if not (self.store.folder / "ids.toml").is_file():
            self.store.write_ledger(self.store.ledger())
        self.store.write_area(self.store.read_area(area))
        self.store.write_index()
        return areas

    def move(self, ident: str, area: str) -> str:
        """Moves an entry to another area and returns the area it left.

        @throws RefusedChangeError When the area is unknown.
        """
        self._known_area(area)
        located = self.store.find(ident)
        source = self.store.read_area(located.area)
        source.drop(ident)
        target = self.store.read_area(area)
        target.put(located.entry)
        self.store.write_area(source)
        self._save(target)
        return located.area

    def merge_areas(self, into: str, source: str) -> int:
        """Moves every entry of one area into another, deletes the emptied area, and returns the count.

        @throws RefusedChangeError When either area is unknown or they are the same.
        """
        self._known_area(into)
        self._known_area(source)
        if into == source:
            raise RefusedChangeError("an area is not merged into itself")
        moving = self.store.read_area(source)
        target = self.store.read_area(into)
        for entry in moving.entries():
            target.put(entry)
        self.store.write_area(target)
        self.store.area_path(source).unlink(missing_ok=True)
        config = self.store.config()
        self.store.write_config(
            BacklogConfig(tuple(area for area in config.areas if area != source), config.pins))
        self.store.write_index()
        return len(moving.entries())

    def _known_area(self, area: str) -> None:
        """Raises when the area is not configured."""
        if area not in self.store.config().areas:
            raise RefusedChangeError(
                f"'{area}' is not an area; the areas are {', '.join(self.store.config().areas)}")

    def _add(self, area: str, prefix: str, build: Callable[[str], AnyEntry]) -> AnyEntry:
        """Takes the next ID of a kind, builds the entry, refuses it on a problem and writes it."""
        self._known_area(area)
        ledger = self.store.ledger()
        entry = build(ledger.take(prefix))
        _refuse_problems(entry)
        parsed = self.store.read_area(area)
        parsed.put(entry)
        self.store.write_ledger(ledger)
        self._save(parsed)
        return entry

    def _write_pins(self, config: BacklogConfig, pins: tuple[str, ...]) -> tuple[str, ...]:
        """Writes the pins and the index."""
        self.store.write_config(BacklogConfig(config.areas, pins))
        self.store.write_index()
        return pins

    def _save(self, area: AreaFile) -> None:
        """Writes an area file and the index."""
        self.store.write_area(area)
        self.store.write_index()


def _refuse_problems(entry: AnyEntry) -> None:
    """Raises when the entry breaks a rule of its kind."""
    problems = entry.problems()
    if problems:
        raise RefusedChangeError(f"{entry.ident}: " + "; ".join(problems))


def _source(value: str) -> str:
    """Returns a Source cell: a bare path is put in backticks, the section mark kept."""
    text = value.strip()
    if not text or text.startswith("`"):
        return text
    path, mark, section = text.partition(" §")
    return f"`{path}`" + (f" §{section}" if mark else "")
