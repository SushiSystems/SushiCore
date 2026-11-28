# triage.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Finds the work that has outlived the triage age, for the owner to keep, reprioritise or drop.

The rule is in `docs/reference/BACKLOG.md`, section "Flow and triage".
"""

from __future__ import annotations

import datetime
from collections.abc import Iterable
from dataclasses import dataclass
from typing import final

from .history import PathChange, changes_after
from .model import WorkEntry, id_number
from .order import age
from .store import AnyEntry

K_TRIAGE_DAYS = 14


@final
@dataclass(frozen=True, slots=True)
class StaleWork:
    """Holds one work entry past the triage age and the commits that changed its Source since it opened."""

    entry: WorkEntry
    touches: int


def stale_work(
    entries: Iterable[AnyEntry], changes: Iterable[PathChange], today: datetime.date,
    days: int = K_TRIAGE_DAYS,
) -> list[StaleWork]:
    """Returns the work entries opened more than *days* ago, the oldest first, then by ID."""
    recorded = list(changes)
    old = [
        entry for entry in entries
        if isinstance(entry, WorkEntry) and age(entry, today) > days
    ]
    old.sort(key=lambda entry: (entry.opened, id_number(entry.ident)))
    return [StaleWork(entry, changes_after(entry.source, entry.opened, recorded)) for entry in old]
