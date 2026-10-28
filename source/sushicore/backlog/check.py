# check.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Every rule `backlog check` enforces on a repository's `docs/backlog/`.

Each rule is a function of one `BacklogCheck` and yields the faults it finds. The rules are in
`docs/reference/BACKLOG.md`, section "Check".
"""

from __future__ import annotations

import datetime
from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass, field
from pathlib import Path

from .errors import BacklogError
from .model import (
    K_REFERENCE,
    WorkEntry,
    id_number,
    source_path,
)
from .order import is_late, is_ready
from .store import (
    K_CONFIG,
    K_DETAIL,
    K_IDS,
    K_INDEX,
    K_PIN_CEILING,
    AreaFile,
    BacklogConfig,
    BacklogStore,
    Fault,
    IdLedger,
    Located,
    is_area_name,
    parse_area,
    render_area,
)

K_RETIRED = (Path("docs/design/REMAINING_WORK.md"), Path("docs/reference/KNOWN_ISSUES.md"))


@dataclass(slots=True)
class BacklogCheck:
    """What one run of the check reads from a repository, read once and shared by the rules."""

    store: BacklogStore
    open_designs: Callable[[], Iterable[Path]] = lambda: ()
    config: BacklogConfig | None = None
    ledger: IdLedger | None = None
    areas: list[AreaFile] = field(default_factory=list)
    located: list[Located] = field(default_factory=list)
    faults: list[Fault] = field(default_factory=list)

    def load(self) -> None:
        """Reads the configuration, the counters and every area file, keeping the faults."""
        folder = self.store.folder
        try:
            self.config = self.store.config()
            self.ledger = self.store.ledger()
        except BacklogError as error:
            self.faults.append(Fault(folder / K_CONFIG, 1, str(error)))
            return
        for area in self.config.areas:
            path = self.store.area_path(area)
            if not path.is_file():
                self.faults.append(Fault(path, 1, f"the area {area} has no file; `backlog check` cannot read it"))
                continue
            text = path.read_text(encoding="utf-8")
            parsed, faults = parse_area(path, text)
            self.faults += faults
            if not faults and render_area(parsed) != text:
                self.faults.append(Fault(path, 1, "the file is not in the shape the tool writes; edit it through `backlog`"))
            self.areas.append(parsed)
            self.located += [
                Located(entry, path, parsed.lines.get(entry.ident, 1), area)
                for entry in parsed.entries()
            ]

    def work(self) -> list[WorkEntry]:
        """Returns every work entry."""
        return [item.entry for item in self.located if isinstance(item.entry, WorkEntry)]

    def ids(self) -> set[str]:
        """Returns the ID of every entry."""
        return {item.entry.ident for item in self.located}


def rule_retired_files(check: BacklogCheck) -> Iterator[Fault]:
    """Yields a fault for each file the store replaced that is still in the repository."""
    for relative in K_RETIRED:
        path = check.store.root / relative
        if path.is_file():
            yield Fault(path, 1, "the store in docs/backlog/ replaced this file; run `backlog import`")


def rule_shape(check: BacklogCheck) -> Iterator[Fault]:
    """Yields each fault reading found: the configuration, the counters, a file or a row."""
    yield from check.faults


def rule_files(check: BacklogCheck) -> Iterator[Fault]:
    """Yields a fault for an area that is not a name, and a file the store does not know."""
    if check.config is None:
        return
    folder = check.store.folder
    known = {K_CONFIG, K_IDS, K_INDEX, *(f"{area}.md" for area in check.config.areas)}
    for area in check.config.areas:
        if not is_area_name(area):
            yield Fault(folder / K_CONFIG, 1, f"'{area}' is not an area name: upper case words joined by _")
    for path in sorted(folder.iterdir()):
        if path.name not in known and path.name != K_DETAIL:
            yield Fault(path, 1, "not a file of the store; an area is named in backlog.toml")


def rule_values(check: BacklogCheck) -> Iterator[Fault]:
    """Yields a fault for each value of an entry that breaks a rule of its kind."""
    for item in check.located:
        for problem in item.entry.problems():
            yield Fault(item.path, item.line, f"{item.entry.ident}: {problem}")


def rule_ids(check: BacklogCheck) -> Iterator[Fault]:
    """Yields a fault for an ID used twice, at or past its counter, or already closed."""
    if check.ledger is None:
        return
    seen: dict[str, Located] = {}
    for item in check.located:
        ident = item.entry.ident
        if ident in seen:
            yield Fault(item.path, item.line, f"{ident}: the ID is used twice; run `backlog renumber`")
            continue
        seen[ident] = item
        try:
            number = id_number(ident)
        except BacklogError:
            continue
        if number >= check.ledger.next[ident[:2]]:
            yield Fault(item.path, item.line, f"{ident}: at or past the counter in ids.toml; run `backlog renumber`")
        elif check.ledger.is_closed(ident):
            yield Fault(item.path, item.line, f"{ident}: the ID was closed and is never reused")


def rule_sources(check: BacklogCheck) -> Iterator[Fault]:
    """Yields a fault for each Source path that does not exist from the repository root."""
    root = check.store.root
    for item in check.located:
        cited = source_path(item.entry.source)
        if cited is not None and (cited.startswith(("/", "..")) or not (root / cited).exists()):
            yield Fault(item.path, item.line, f"{item.entry.ident}: Source '{cited}' does not exist from the repository root")


def rule_references(check: BacklogCheck) -> Iterator[Fault]:
    """Yields a fault for each cited ID that names no open entry, here or in a sibling checked out."""
    ids = check.ids()
    for item in check.located:
        for reference in item.entry.cited():
            match = K_REFERENCE.match(reference)
            if match is None:
                continue
            resolved = _resolves(check.store.root, ids, match["owner"], match["id"])
            if resolved is False:
                yield Fault(item.path, item.line, f"{item.entry.ident}: '{reference}' names no open entry")


def rule_blocked_ready(check: BacklogCheck) -> Iterator[Fault]:
    """Yields a fault for a blocked entry whose blocks are all closed: it is open now."""
    open_ids = frozenset(check.ids())
    for item in check.located:
        entry = item.entry
        if isinstance(entry, WorkEntry) and entry.state == "blocked" and is_ready(entry, open_ids):
            yield Fault(item.path, item.line, f"{entry.ident}: every block is closed; set State to open")


def rule_sorted(check: BacklogCheck) -> Iterator[Fault]:
    """Yields a fault for a table whose rows are not sorted by ID."""
    for area in check.areas:
        for table in (area.work, area.issues):
            numbers = []
            for entry in table:
                try:
                    numbers.append(id_number(entry.ident))
                except BacklogError:
                    numbers.append(0)
            if numbers != sorted(numbers):
                path = check.store.area_path(area.area)
                yield Fault(path, 1, "the rows of a table are sorted by ID")


def rule_pins(check: BacklogCheck) -> Iterator[Fault]:
    """Yields a fault for more pins than the ceiling, and a pin that names no open work."""
    if check.config is None:
        return
    path = check.store.folder / K_CONFIG
    if len(check.config.pins) > K_PIN_CEILING:
        yield Fault(path, 1, f"{len(check.config.pins)} pins; the ceiling is {K_PIN_CEILING}")
    work = {entry.ident: entry for entry in check.work()}
    for pin in check.config.pins:
        if pin not in work:
            yield Fault(path, 1, f"the pin {pin} names no open work entry")
        elif work[pin].state == "decision":
            yield Fault(path, 1, f"the pin {pin} is a decision; the owner takes it, not an agent")


def rule_details(check: BacklogCheck) -> Iterator[Fault]:
    """Yields a fault for a detail file whose entry is closed."""
    folder = check.store.folder / K_DETAIL
    ids = check.ids()
    for path in sorted(folder.glob("*.md")) if folder.is_dir() else []:
        if path.stem not in ids:
            yield Fault(path, 1, f"{path.stem} is closed; `backlog close` deletes its detail")


def rule_index(check: BacklogCheck) -> Iterator[Fault]:
    """Yields a fault when the generated README.md is not what the entries say."""
    if check.config is None or check.faults:
        return
    path = check.store.folder / K_INDEX
    current = path.read_text(encoding="utf-8") if path.is_file() else None
    if current != check.store.render_index():
        yield Fault(path, 1, "the index is stale; any `backlog` command that writes regenerates it")


def rule_design_coverage(check: BacklogCheck) -> Iterator[Fault]:
    """Yields a fault for each open design topic that no work entry's Source cites."""
    root = check.store.root
    cited = [source_path(entry.source) or "" for entry in check.work()]
    for document in check.open_designs():
        relative = document.relative_to(root).as_posix()
        folder = relative.rsplit("/", 1)[0] + "/"
        if not any(path == relative or path.startswith(folder) for path in cited):
            yield Fault(document, 1, "an open design topic is cited by the Source of a work entry")


K_RULES: dict[str, Callable[[BacklogCheck], Iterator[Fault]]] = {
    "retired_files": rule_retired_files,
    "shape": rule_shape,
    "files": rule_files,
    "values": rule_values,
    "ids": rule_ids,
    "sources": rule_sources,
    "references": rule_references,
    "blocked_ready": rule_blocked_ready,
    "sorted": rule_sorted,
    "pins": rule_pins,
    "details": rule_details,
    "index": rule_index,
    "design_coverage": rule_design_coverage,
}


def check_backlog(
    store: BacklogStore, open_designs: Callable[[], Iterable[Path]] = lambda: (),
) -> list[Fault]:
    """Returns every fault of a repository's backlog; none for a repository without one.

    A repository that still holds the two retired files and no store gets the fault that sends
    it to `backlog import`.
    """
    check = BacklogCheck(store, open_designs)
    if not store.exists():
        return list(rule_retired_files(check))
    check.load()
    found: list[Fault] = []
    for rule in K_RULES.values():
        found += rule(check)
    return found


def late_entries(store: BacklogStore, today: datetime.date) -> list[WorkEntry]:
    """Returns every work entry past the age limit of its priority."""
    return [entry for entry in store.entries() if isinstance(entry, WorkEntry) and is_late(entry, today)]


def _resolves(root: Path, ids: set[str], owner: str | None, ident: str) -> bool | None:
    """Returns whether a reference names an open entry, or None for a sibling not checked out."""
    if owner is None or owner == root.resolve().name:
        return ident in ids
    sibling = root.resolve().parent / owner
    store = BacklogStore(sibling)
    if not store.exists():
        return None
    try:
        return ident in {entry.ident for entry in store.entries()}
    except BacklogError:
        return None
