# order.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""The age of an entry, whether it is late, and the order in which an agent takes work.

The rules are in `docs/reference/BACKLOG.md`, section "Priority and order".
"""

from __future__ import annotations

import datetime
from collections.abc import Iterable

from .model import K_PRIORITIES, IssueEntry, WorkEntry, id_number

K_AGE_LIMITS = {"P0": 2, "P1": 14, "P2": 90, "P3": 180}
K_READY_STATES = frozenset({"open", "unmeasured"})


def age(entry: WorkEntry | IssueEntry, today: datetime.date) -> int:
    """Returns how many days ago the entry was opened."""
    return (today - entry.opened).days


def is_late(entry: WorkEntry, today: datetime.date) -> bool:
    """Returns whether a work entry has passed the age limit of its priority."""
    limit = K_AGE_LIMITS.get(entry.priority)
    return limit is not None and age(entry, today) > limit


def is_ready(entry: WorkEntry, open_ids: frozenset[str]) -> bool:
    """Returns whether an agent can take the entry now.

    An entry is ready when it is open or unmeasured, or blocked only by local entries that are
    no longer open. A decision is never ready; it is the owner's.
    """
    if entry.state in K_READY_STATES:
        return True
    if entry.state != "blocked":
        return False
    blocks = entry.blocks()
    is_local = len(blocks) == len([item for item in entry.blocked_by.split(",") if item.strip()])
    return is_local and all(" " not in item and item not in open_ids for item in blocks)


def next_work(
    entries: Iterable[WorkEntry | IssueEntry],
    pins: Iterable[str],
    today: datetime.date,
    count: int | None = None,
) -> list[WorkEntry]:
    """Returns the work an agent should take, first to last.

    The owner's pins that are ready come first in their listed order; then every other ready
    entry by priority, then by age, the oldest first, then by ID.
    """
    work = [entry for entry in entries if isinstance(entry, WorkEntry)]
    open_ids = frozenset(entry.ident for entry in work)
    by_id = {entry.ident: entry for entry in work}
    pinned = [by_id[ident] for ident in dict.fromkeys(pins) if ident in by_id]
    pinned = [entry for entry in pinned if is_ready(entry, open_ids)]
    rest = sorted(
        (entry for entry in work if entry not in pinned and is_ready(entry, open_ids)),
        key=lambda entry: (_rank(entry.priority), -age(entry, today), id_number(entry.ident)),
    )
    ordered = pinned + rest
    return ordered if count is None else ordered[:count]


def decisions(entries: Iterable[WorkEntry | IssueEntry]) -> list[WorkEntry]:
    """Returns the entries waiting for the owner, by priority, then by ID."""
    found = [entry for entry in entries if isinstance(entry, WorkEntry) and entry.state == "decision"]
    return sorted(found, key=lambda entry: (_rank(entry.priority), id_number(entry.ident)))


def _rank(priority: str) -> int:
    """Returns the place of a priority, an unknown one last."""
    return K_PRIORITIES.index(priority) if priority in K_PRIORITIES else len(K_PRIORITIES)
