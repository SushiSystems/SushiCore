# importer.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Moves a repository's backlog into the store once, and gives clashing IDs new numbers.

`import` reads `docs/design/REMAINING_WORK.md` and `docs/reference/KNOWN_ISSUES.md`, the form
the store replaced, writes `docs/backlog/` and deletes both files. `renumber` resolves two
branches that took the same ID. Both rewrite the citations they change.
"""

from __future__ import annotations

import datetime
import re
import subprocess
from dataclasses import dataclass, field, fields
from pathlib import Path

from ..citations import K_EXTENSIONS, Rewrite, files_citing, repair_citations
from .errors import BacklogError
from .model import (
    K_EXTERNAL,
    K_FIX,
    K_ISSUE_PREFIX,
    K_ORIGINS,
    K_REFERENCE,
    K_SOURCE,
    K_STATES,
    K_TITLE_CEILING,
    K_DONE_WHEN_CEILING,
    K_CELL_CEILING,
    K_WORK_PREFIX,
    IssueEntry,
    WorkEntry,
    id_number,
    split_references,
)
from .store import (
    K_FOLDER,
    K_IDS,
    K_INDEX,
    K_PIN_CEILING,
    AnyEntry,
    AreaFile,
    BacklogConfig,
    BacklogStore,
    IdLedger,
    parse_area,
    parse_ranges,
)

K_LEGACY_WORK = Path("docs/design/REMAINING_WORK.md")
K_LEGACY_ISSUES = Path("docs/reference/KNOWN_ISSUES.md")
K_NEXT_SECTION = "Next"
K_DECISIONS_SECTION = "Decisions waiting for the owner"
K_FALLBACK_AREA = "GENERAL"
K_DEFAULT_PRIORITY = "P2"
K_PINNED_PRIORITY = "P1"
K_ROW_FIELDS = {
    K_WORK_PREFIX: frozenset({"State", "Done when", "Blocked by"}),
    K_ISSUE_PREFIX: frozenset({"Origin", "Upstream", "Workaround", "Fix"}),
}
K_STOP_WORDS = frozenset({"a", "an", "and", "the", "of", "for", "this", "to", "in", "on", "with"})
K_COUNTER = re.compile(r"^Next id: (RW|KI)-(\d+)$")
K_HEADING = re.compile(r"^### (RW|KI)-(\d+)\s+(.*\S)\s*$")
K_NEXT_LINE = re.compile(r"^- (RW-\d+)\b")
K_FIELD = re.compile(r"^- ([A-Z][a-z]+(?: [a-z]+)?): (.*)$")
K_CONTINUATION = re.compile(r"^  \S")
K_FENCE = re.compile(r"^(`{3,}|~{3,})")
K_WORD = re.compile(r"[A-Za-z0-9]+")
K_ELLIPSIS = "…"
K_PAGE_SUFFIXES = frozenset({".md"})


@dataclass(slots=True)
class LegacyEntry:
    """One entry of the retired form: its heading, its fields and the prose after them."""

    ident: str
    title: str
    section: str
    line: int
    fields: dict[str, str] = field(default_factory=dict)
    order: list[str] = field(default_factory=list)
    prose: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class ImportResult:
    """What `import` wrote: the entries per kind, the detail files, the pins and the citations.

    `left` holds the source and build files that still name a retired file: a path a program
    holds is changed by its author, not by the import.
    """

    work: int
    issues: int
    details: int
    pins: tuple[str, ...]
    areas: tuple[str, ...]
    rewrites: tuple[Rewrite, ...]
    left: tuple[Path, ...] = ()


@dataclass(frozen=True, slots=True)
class RenumberResult:
    """What `renumber` changed: each old ID with its new one, for the caller to cite."""

    renames: tuple[tuple[str, str], ...]


def read_legacy(path: Path) -> tuple[int, list[LegacyEntry], list[str]]:
    """Returns the counter, the entries and the `## Next` IDs of one retired file."""
    counter = 1
    entries: list[LegacyEntry] = []
    pins: list[str] = []
    section = ""
    current: LegacyEntry | None = None
    is_fenced = False
    is_in_fields = False
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if K_FENCE.match(line):
            is_fenced = not is_fenced
        if not is_fenced and line.startswith("## "):
            section, current = line[3:].strip(), None
            continue
        match = K_COUNTER.match(line)
        if match and current is None:
            counter = int(match[2])
            continue
        heading = None if is_fenced else K_HEADING.match(line)
        if heading:
            current = LegacyEntry(f"{heading[1]}-{heading[2]}", heading[3], section, number)
            entries.append(current)
            is_in_fields = True
            continue
        if current is None:
            next_line = K_NEXT_LINE.match(line)
            if section == K_NEXT_SECTION and next_line:
                pins.append(next_line[1])
            continue
        field_match = K_FIELD.match(line) if is_in_fields else None
        if field_match:
            name = field_match[1]
            current.fields[name] = field_match[2].strip()
            current.order.append(name)
        elif is_in_fields and current.order and K_CONTINUATION.match(line):
            name = current.order[-1]
            current.fields[name] = f"{current.fields[name]} {line.strip()}"
        else:
            is_in_fields = False
            current.prose.append(line)
    return counter, entries, pins


def area_key(section: str) -> str:
    """Returns the area a section of the retired form becomes: `Physics and matter` is `PHYSICS_MATTER`."""
    words = [word.upper() for word in K_WORD.findall(section) if word.lower() not in K_STOP_WORDS]
    key = "_".join(words)
    if not key or not key[0].isalpha():
        return K_FALLBACK_AREA
    return key


class BacklogImporter:
    """Writes the store from the retired files of one repository and deletes them."""

    def __init__(self, store: BacklogStore) -> None:
        """Keeps the store the import writes."""
        self.store = store
        self.root = store.root

    def run(self) -> ImportResult:
        """Imports both files, writes the store and the index, and rewrites their citations.

        @throws BacklogError When the store already exists or there is nothing to import.
        """
        if self.store.exists():
            raise BacklogError(f"{self.store.folder} exists; import runs once")
        work_path, issue_path = self.root / K_LEGACY_WORK, self.root / K_LEGACY_ISSUES
        if not work_path.is_file() and not issue_path.is_file():
            raise BacklogError(f"neither {K_LEGACY_WORK} nor {K_LEGACY_ISSUES} exists")
        ledger = IdLedger()
        areas: dict[str, AreaFile] = {}
        pins: list[str] = []
        details = 0
        counts = {K_WORK_PREFIX: 0, K_ISSUE_PREFIX: 0}
        for prefix, path in ((K_WORK_PREFIX, work_path), (K_ISSUE_PREFIX, issue_path)):
            if not path.is_file():
                continue
            counter, legacy, next_ids = read_legacy(path)
            dates = _blame_dates(path)
            pins += next_ids
            numbers = set()
            for item in legacy:
                if not item.ident.startswith(prefix):
                    continue
                numbers.add(id_number(item.ident))
                opened = dates.get(item.line, self.store.today())
                entry, has_detail = self._convert(item, path, opened, item.ident in next_ids)
                if has_detail:
                    details += 1
                key = K_FALLBACK_AREA if item.section == K_DECISIONS_SECTION else area_key(item.section)
                areas.setdefault(key, AreaFile(key)).put(entry)
                counts[prefix] += 1
            ledger.next[prefix] = max([counter, *(number + 1 for number in numbers)])
            ledger.closed[prefix] = set(range(1, ledger.next[prefix])) - numbers
        open_work = {entry.ident for area in areas.values() for entry in area.work}
        kept_pins = tuple(dict.fromkeys(pin for pin in pins if pin in open_work))[:K_PIN_CEILING]
        names = tuple(sorted(areas))
        self.store.write_config(BacklogConfig(names, kept_pins))
        self.store.write_ledger(ledger)
        for area in areas.values():
            self.store.write_area(area)
        self.store.write_index()
        for path in (work_path, issue_path):
            if path.is_file():
                path.unlink()
        moves = {
            K_LEGACY_WORK.as_posix(): (K_FOLDER / K_INDEX).as_posix(),
            K_LEGACY_ISSUES.as_posix(): (K_FOLDER / K_INDEX).as_posix(),
        }
        rewrites = repair_citations(self.root, {}, moves, apply=True, suffixes=K_PAGE_SUFFIXES)
        left = files_citing(self.root, list(moves), K_EXTENSIONS - K_PAGE_SUFFIXES)
        return ImportResult(
            counts[K_WORK_PREFIX], counts[K_ISSUE_PREFIX], details, kept_pins, names,
            tuple(rewrite for rewrite in rewrites if rewrite.old in moves), tuple(left),
        )

    def _convert(
        self, item: LegacyEntry, path: Path, opened: datetime.date, is_pinned: bool,
    ) -> tuple[AnyEntry, bool]:
        """Returns the row an entry of the retired form becomes, and whether it needed a detail file."""
        overflow: list[str] = []
        title = _fit(item.title, K_TITLE_CEILING, overflow)
        source = item.fields.get("Source", "")
        if source and not K_SOURCE.match(source):
            overflow.append("source")
            source = ""
        extra = [name for name in item.order if name not in K_ROW_FIELDS[item.ident[:2]] and name != "Source"]
        prose = [line for line in item.prose if line.strip()]
        if item.ident.startswith(K_WORK_PREFIX):
            entry: AnyEntry = self._work(item, title, opened, is_pinned, overflow)
        else:
            entry = self._issue(item, title, opened, overflow)
        has_detail = bool(overflow or extra or prose)
        if has_detail:
            self.store.write_detail(item.ident, _detail_text(item, self.store.relative(entry_path(self.store, item))))
        if source:
            entry = entry.__class__(**{**_fields(entry), "source": source})
        return entry, has_detail

    def _work(
        self, item: LegacyEntry, title: str, opened: datetime.date, is_pinned: bool,
        overflow: list[str],
    ) -> WorkEntry:
        """Returns the work row of a legacy entry."""
        state = item.fields.get("State", "open")
        if state not in K_STATES:
            overflow.append("state")
            state = "open"
        blocked = item.fields.get("Blocked by", "")
        if blocked and not all(
            K_REFERENCE.match(part) or K_EXTERNAL.match(part) for part in split_references(blocked)
        ):
            overflow.append("blocked by")
            blocked = _fit(f"external: {blocked}", K_CELL_CEILING, overflow)
        if state == "blocked" and not blocked:
            blocked = "external: not recorded"
        if state != "blocked" and blocked:
            overflow.append("blocked by")
            blocked = ""
        done_when = item.fields.get("Done when", "") or "the detail's criterion holds"
        priority = K_PINNED_PRIORITY if is_pinned else K_DEFAULT_PRIORITY
        return WorkEntry(
            item.ident, priority, state, title, _fit(done_when, K_DONE_WHEN_CEILING, overflow),
            blocked, "", opened,
        )

    def _issue(
        self, item: LegacyEntry, title: str, opened: datetime.date, overflow: list[str],
    ) -> IssueEntry:
        """Returns the issue row of a legacy entry."""
        origin = item.fields.get("Origin", "own")
        upstream = item.fields.get("Upstream", "")
        if origin not in K_ORIGINS:
            match = K_REFERENCE.match(upstream)
            origin = upstream if match and match["owner"] and match["id"].startswith("KI-") else "dependency"
            overflow.append("origin")
        workaround = _fit(item.fields.get("Workaround", "") or "none", K_CELL_CEILING, overflow)
        if workaround.lower().startswith("none"):
            workaround = "none" if workaround.lower().rstrip(".") == "none" else workaround
        fix = item.fields.get("Fix", "")
        if fix and not K_FIX.match(fix):
            overflow.append("fix")
            fix = "none, see the detail"
        fix = _fit(fix, K_CELL_CEILING, overflow)
        if origin == "own" and not fix:
            fix = "none, not recorded"
        return IssueEntry(item.ident, origin, title, workaround, fix, "", opened)


def entry_path(store: BacklogStore, item: LegacyEntry) -> Path:
    """Returns the area file an imported entry lands in."""
    key = K_FALLBACK_AREA if item.section == K_DECISIONS_SECTION else area_key(item.section)
    return store.area_path(key)


class BacklogRenumberer:
    """Gives each entry that shares an ID with a different entry the next free number."""

    def __init__(self, store: BacklogStore, target: str = "main") -> None:
        """Keeps the store and the branch whose entries keep their IDs."""
        self.store = store
        self.target = target

    def run(self) -> RenumberResult:
        """Reads every area file across merge conflicts, renumbers, and writes the store back.

        The entry the target branch holds keeps its ID; the other takes the next free number.
        """
        target_rows = self._target_rows()
        ledger = self._merged_ledger()
        areas: list[AreaFile] = []
        holders: dict[str, list[tuple[AreaFile, AnyEntry]]] = {}
        for name in self.store.config().areas:
            path = self.store.area_path(name)
            area = AreaFile(name)
            areas.append(area)
            if not path.is_file():
                continue
            parsed, _ = parse_area(path, path.read_text(encoding="utf-8"), tolerate_conflicts=True)
            for entry in parsed.entries():
                found = holders.setdefault(entry.ident, [])
                if all(other != entry for _, other in found):
                    found.append((area, entry))
        for ident in holders:
            ledger.next[ident[:2]] = max(ledger.next[ident[:2]], id_number(ident) + 1)
        renames: list[tuple[str, str]] = []
        for ident, found in sorted(holders.items(), key=lambda item: (item[0][:2], id_number(item[0]))):
            kept = next(
                (index for index, (_, entry) in enumerate(found) if entry.cells() == target_rows.get(ident)),
                0,
            )
            for index, (area, entry) in enumerate(found):
                if index == kept:
                    area.put(entry)
                    continue
                new = ledger.take(ident[:2])
                renames.append((ident, new))
                area.put(entry.__class__(**{**_fields(entry), "ident": new}))
        for area in areas:
            self.store.write_area(area)
        self.store.write_ledger(ledger)
        self.store.write_index()
        return RenumberResult(tuple(renames))

    def _target_rows(self) -> dict[str, list[str]]:
        """Returns the cells of every row the target branch holds, by ID."""
        found: dict[str, list[str]] = {}
        for name in self.store.config().areas:
            relative = self.store.relative(self.store.area_path(name))
            text = _git_show(self.store.root, f"{self.target}:{relative}")
            if text:
                parsed, _ = parse_area(self.store.area_path(name), text, tolerate_conflicts=True)
                found.update({entry.ident: entry.cells() for entry in parsed.entries()})
        return found

    def _merged_ledger(self) -> IdLedger:
        """Returns the counters with every side of a conflict in `ids.toml` taken at its highest."""
        path = self.store.folder / K_IDS
        ledger = IdLedger()
        prefix = K_WORK_PREFIX
        for line in path.read_text(encoding="utf-8").splitlines() if path.is_file() else []:
            name, _, value = (part.strip() for part in line.partition("="))
            if line.startswith("["):
                prefix = K_WORK_PREFIX if line.strip() == "[work]" else K_ISSUE_PREFIX
            elif name == "next":
                ledger.next[prefix] = max(ledger.next[prefix], int(value))
            elif name == "closed":
                ledger.closed[prefix] |= parse_ranges(value.strip('"'))
        return ledger


def _fit(text: str, ceiling: int, overflow: list[str]) -> str:
    """Returns the text cut at a word to fit the ceiling, recording the cut in *overflow*."""
    text = " ".join(text.split())
    if len(text) <= ceiling:
        return text
    overflow.append("length")
    cut = text[: ceiling - 1].rsplit(" ", 1)[0].rstrip(",;:")
    return f"{cut}{K_ELLIPSIS}"


def _fields(entry: AnyEntry) -> dict[str, object]:
    """Returns the fields of an entry by name."""
    return {item.name: getattr(entry, item.name) for item in fields(entry)}


def _detail_text(item: LegacyEntry, area: str) -> str:
    """Returns the detail file of an imported entry: its full heading, its fields and its prose."""
    lines = [
        f"# {item.ident} {item.title}",
        "",
        f"The row of this entry is in `{area}`. This file holds what did not fit the row.",
        "",
    ]
    lines += [f"- {name}: {item.fields[name]}" for name in item.order]
    prose = list(item.prose)
    while prose and not prose[-1].strip():
        prose.pop()
    while prose and not prose[0].strip():
        prose.pop(0)
    if prose:
        lines += ["", *prose]
    return "\n".join(lines) + "\n"


def _blame_dates(path: Path) -> dict[int, datetime.date]:
    """Returns the date each line of a file was written, from git; empty outside a repository."""
    try:
        completed = subprocess.run(
            ["git", "-C", str(path.parent), "blame", "--line-porcelain", "--", path.name],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
    except OSError:
        return {}
    if completed.returncode != 0:
        return {}
    dates: dict[int, datetime.date] = {}
    line = 0
    stamp = 0
    for text in completed.stdout.splitlines():
        parts = text.split(" ")
        if len(parts) >= 3 and len(parts[0]) == 40 and parts[1].isdigit():
            line = int(parts[2])
        elif text.startswith("author-time "):
            stamp = int(parts[1])
        elif text.startswith("\t"):
            dates[line] = datetime.date.fromtimestamp(stamp)
    return dates


def _git_show(root: Path, spec: str) -> str:
    """Returns a file of another revision, or an empty string when git cannot show it."""
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), "show", spec],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
    except OSError:
        return ""
    return completed.stdout if completed.returncode == 0 else ""
