# test_order.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests the age limits and the order `next` gives."""

from __future__ import annotations

import datetime

import pytest

from sushicore.backlog import WorkEntry, decisions, is_late, next_work

pytestmark = pytest.mark.small

K_TODAY = datetime.date(2026, 10, 28)


def _work(
    ident: str, priority: str = "P2", state: str = "open", days: int = 0, blocked_by: str = "",
) -> WorkEntry:
    """Returns a work entry opened some days before today."""
    opened = K_TODAY - datetime.timedelta(days=days)
    return WorkEntry(ident, priority, state, "Do it", "it is done", blocked_by, "", opened)


@pytest.mark.parametrize(
    "priority, days, late",
    [("P0", 2, False), ("P0", 3, True), ("P1", 15, True), ("P2", 90, False), ("P3", 181, True)],
)
def test_an_entry_is_late_past_its_priority_limit(priority, days, late):
    """Each priority has its own age limit."""
    assert is_late(_work("RW-1", priority, days=days), K_TODAY) is late


def test_next_orders_by_priority_then_age_then_id():
    """Higher priority first; inside a priority, the oldest first."""
    entries = [
        _work("RW-1", "P2", days=50), _work("RW-2", "P1", days=1),
        _work("RW-3", "P2", days=80), _work("RW-4", "P2", days=80),
    ]
    assert [e.ident for e in next_work(entries, (), K_TODAY)] == ["RW-2", "RW-3", "RW-4", "RW-1"]


def test_pins_come_first_in_their_order():
    """The owner's pins lead, in the order listed."""
    entries = [_work("RW-1", "P0"), _work("RW-2", "P3"), _work("RW-3", "P3")]
    order = next_work(entries, ("RW-3", "RW-2"), K_TODAY)
    assert [e.ident for e in order] == ["RW-3", "RW-2", "RW-1"]


def test_decisions_and_open_blocks_are_never_returned():
    """A decision is the owner's; a block on an open entry holds the work back, even pinned."""
    entries = [
        _work("RW-1", state="decision"), _work("RW-2"),
        _work("RW-3", state="blocked", blocked_by="RW-2"),
    ]
    assert [e.ident for e in next_work(entries, ("RW-3", "RW-1"), K_TODAY)] == ["RW-2"]


def test_a_block_on_a_closed_entry_releases_the_work():
    """When every block is closed the blocked entry is ready."""
    entries = [_work("RW-3", state="blocked", blocked_by="RW-2")]
    assert [e.ident for e in next_work(entries, (), K_TODAY)] == ["RW-3"]


def test_external_and_sibling_blocks_hold_the_work():
    """A block outside the repository is never known to be closed."""
    entries = [
        _work("RW-3", state="blocked", blocked_by="external: vendor"),
        _work("RW-4", state="blocked", blocked_by="sushiweb RW-1"),
    ]
    assert next_work(entries, (), K_TODAY) == []


def test_count_cuts_the_list_and_decisions_lists_the_owners():
    """`count` keeps the first entries; `decisions` lists only decisions, by priority."""
    entries = [
        _work("RW-1"), _work("RW-2"),
        _work("RW-5", "P1", state="decision"), _work("RW-6", "P0", state="decision"),
    ]
    assert len(next_work(entries, (), K_TODAY, 1)) == 1
    assert [e.ident for e in decisions(entries)] == ["RW-6", "RW-5"]
