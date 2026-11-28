# test_triage.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests the triage list: the work past the triage age, oldest first, with the commits to its Source."""

from __future__ import annotations

import datetime

import pytest

from sushicore.backlog import IssueEntry, WorkEntry, stale_work
from sushicore.backlog.history import PathChange

pytestmark = pytest.mark.small

K_TODAY = datetime.date(2026, 11, 28)


def _work(ident: str, age: int, source: str = "`src/a.cpp`") -> WorkEntry:
    """Returns an open work entry opened *age* days ago."""
    return WorkEntry(ident, "P2", "open", "Fix it", "it passes", "", source, K_TODAY - datetime.timedelta(days=age))


def test_stale_work_keeps_the_work_past_the_age_oldest_first():
    """Fourteen days old is still inside the age; an issue is never triaged as work."""
    issue = IssueEntry("KI-1", "own", "It drifts", "restart", "none, by design", "", K_TODAY - datetime.timedelta(days=90))
    entries = [_work("RW-3", 15), _work("RW-1", 14), _work("RW-2", 40), issue]
    found = [item.entry.ident for item in stale_work(entries, [], K_TODAY, 14)]
    assert found == ["RW-2", "RW-3"]


def test_stale_work_counts_the_commits_to_the_source_after_the_entry_opened():
    """A commit to the place of the work after it opened shows work that was touched and left open."""
    changes = [PathChange(K_TODAY - datetime.timedelta(days=day), ("src/a.cpp",)) for day in (40, 20, 3)]
    [item] = stale_work([_work("RW-1", 30)], changes, K_TODAY, 14)
    assert item.touches == 2
