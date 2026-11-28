# flow.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Measures the flow of remaining work: what opened and closed in a window, and what was left behind.

The measures are in `docs/reference/BACKLOG.md`, section "Flow and triage".
"""

from __future__ import annotations

import datetime
from dataclasses import asdict, dataclass
from typing import final

from .admission import K_DOCS_PREFIX
from .history import Recorded, changes_after
from .model import source_path

K_FLOW_DAYS = 14


@final
@dataclass(frozen=True, slots=True)
class Flow:
    """Holds the measures of one window of days ending today."""

    days: int
    opened: int
    closed: int
    closed_same_day: int
    open_now: int
    changed_and_open: int

    def payload(self) -> dict[str, int]:
        """Returns the measures as a JSON object."""
        return asdict(self)

    def lines(self) -> list[str]:
        """Returns the measures as lines of text."""
        return [
            f"window: the last {self.days} days",
            f"opened: {self.opened}",
            f"closed: {self.closed}",
            f"closed the day they opened: {self.closed_same_day}",
            f"open now: {self.open_now}",
            f"open, with a later commit to their Source: {self.changed_and_open}",
        ]


def measure_flow(recorded: Recorded, today: datetime.date, days: int = K_FLOW_DAYS) -> Flow:
    """Returns the flow of remaining work in the *days* that end on *today*.

    `changed_and_open` counts the open work whose Source, outside `docs/`, a commit changed on a
    day after the entry opened: work an agent touched and did not close.
    """
    start = today - datetime.timedelta(days=days)
    work = [life for life in recorded.lives if life.is_work]
    opened = [life for life in work if life.opened > start]
    closed = [life for life in work if life.closed is not None and life.closed > start]
    still_open = [life for life in work if life.closed is None]
    changed = [
        life for life in still_open
        if not (source_path(life.source) or K_DOCS_PREFIX).startswith(K_DOCS_PREFIX)
        and changes_after(life.source, life.opened, recorded.changes) > 0
    ]
    return Flow(
        days=days,
        opened=len(opened),
        closed=len(closed),
        closed_same_day=len([life for life in opened if life.closed == life.opened]),
        open_now=len(still_open),
        changed_and_open=len(changed),
    )
