# renumber.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Resolves two branches of the backlog that conflicted in its counters or took the same ID.

`renumber` reads both sides of every conflict in `docs/backlog/`, gives each entry that shares
an ID with a different one the next free number, and writes the store back with its index.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import final

from ..proc import CommandRunner
from ..quiet_runner import quiet_runner
from .model import K_ISSUE_PREFIX, K_WORK_PREFIX, id_number
from .store import (
    K_IDS,
    AnyEntry,
    AreaFile,
    BacklogStore,
    IdLedger,
    parse_area,
    parse_ranges,
)


@final
@dataclass(frozen=True, slots=True)
class RenumberResult:
    """What `renumber` changed: each old ID with its new one, for the caller to cite."""

    renames: tuple[tuple[str, str], ...]


@final
class BacklogRenumberer:
    """Gives each entry that shares an ID with a different entry the next free number."""

    def __init__(self, store: BacklogStore, target: str = "main",
                 runner: CommandRunner | None = None) -> None:
        """Keeps the store, the branch whose entries keep their IDs and the runner that asks git."""
        self.store = store
        self.target = target
        self._runner = runner if runner is not None else quiet_runner()

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
                area.put(replace(entry, ident=new))
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
            text = _git_show(self.store.root, f"{self.target}:{relative}", self._runner)
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


def _git_show(root: Path, spec: str, runner: CommandRunner) -> str:
    """Returns a file of another revision, or an empty string when git cannot show it."""
    try:
        code, stdout, _ = runner.capture(["git", "-C", str(root), "show", spec], encoding="utf-8")
    except OSError:
        return ""
    return stdout if code == 0 else ""
