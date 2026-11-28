# test_flow.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests the flow of remaining work over a window: opened, closed, closed the same day, and changed but open."""

from __future__ import annotations

import datetime

import pytest

from sushicore.backlog import Recorded, measure_flow
from sushicore.backlog.history import EntryLife, PathChange

pytestmark = pytest.mark.small

K_TODAY = datetime.date(2026, 11, 28)


def _day(offset: int) -> datetime.date:
    """Returns the day *offset* days before today."""
    return K_TODAY - datetime.timedelta(days=offset)


def _recorded() -> Recorded:
    """Returns a history with one entry of each fate and a commit to the Source of two open ones."""
    lives = [
        EntryLife("RW-1", _day(40), "`src/old.cpp`"),
        EntryLife("RW-2", _day(10), "`src/a.cpp`", closed=_day(10)),
        EntryLife("RW-3", _day(9), "`src/b.cpp`", closed=_day(2)),
        EntryLife("RW-4", _day(5), "`src/c.cpp`"),
        EntryLife("RW-5", _day(5), "`docs/design/C.md`"),
        EntryLife("KI-1", _day(5), "`src/c.cpp`"),
    ]
    changes = [
        PathChange(_day(30), ("src/old.cpp",)),
        PathChange(_day(3), ("src/c.cpp", "docs/design/C.md")),
    ]
    return Recorded(lives, changes)


def test_measure_flow_counts_the_work_of_the_window():
    """Issues are left out; RW-1 opened before the window, so it counts only as open."""
    flow = measure_flow(_recorded(), K_TODAY, 14)
    found = (flow.opened, flow.closed, flow.closed_same_day, flow.open_now)
    assert found == (4, 2, 1, 3)


def test_measure_flow_counts_the_open_work_a_later_commit_changed():
    """RW-1 and RW-4 had their code changed after they opened; RW-5 cites a page, which is no place of work."""
    assert measure_flow(_recorded(), K_TODAY, 14).changed_and_open == 2


def test_measure_flow_lines_name_each_measure():
    """The text form prints one measure a line, the window first."""
    lines = measure_flow(_recorded(), K_TODAY, 14).lines()
    assert lines[0] == "window: the last 14 days"
    assert lines[-1] == "open, with a later commit to their Source: 2"
