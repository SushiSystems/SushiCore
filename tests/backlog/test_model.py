# test_model.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests the two entry kinds: their rows, their values and their ceilings."""

from __future__ import annotations

import datetime

import pytest

from sushicore.backlog import IssueEntry, RowError, WorkEntry
from sushicore.backlog.model import join_row, split_row

pytestmark = pytest.mark.small

K_DAY = datetime.date(2026, 10, 1)


def _work(**changes) -> WorkEntry:
    """Returns a valid work entry with some values changed."""
    values = dict(
        ident="RW-4", priority="P1", state="open", title="Fix the step",
        done_when="the step test passes", blocked_by="", source="", opened=K_DAY,
    )
    values.update(changes)
    return WorkEntry(**values)


def _issue(**changes) -> IssueEntry:
    """Returns a valid known issue with some values changed."""
    values = dict(
        ident="KI-2", origin="own", symptom="The link fails", workaround="link twice",
        fix="RW-4", source="", opened=K_DAY,
    )
    values.update(changes)
    return IssueEntry(**values)


def test_row_round_trip_keeps_a_pipe_inside_a_cell():
    """A cell holding a pipe is escaped on write and read back whole."""
    entry = _work(title="Read a | b")
    line = join_row(entry.cells())
    assert "\\|" in line
    assert WorkEntry.from_cells(split_row(line)) == entry


def test_from_cells_rejects_a_row_with_a_cell_missing():
    """A row with seven cells is not a work entry."""
    with pytest.raises(RowError):
        WorkEntry.from_cells(_work().cells()[:-1])


def test_from_cells_rejects_a_date_that_is_not_iso():
    """Opened holds an ISO date."""
    cells = _work().cells()
    cells[-1] = "28/10/2026"
    with pytest.raises(RowError):
        WorkEntry.from_cells(cells)


def test_valid_work_has_no_problem():
    """A filled entry within its ceilings passes."""
    assert _work().problems() == []


@pytest.mark.parametrize(
    "changes, fragment",
    [
        ({"priority": "P5"}, "Pri"),
        ({"state": "done"}, "State"),
        ({"title": "x" * 91}, "Title is 91"),
        ({"done_when": "x" * 161}, "Done when is 161"),
        ({"state": "blocked"}, "Blocked by"),
        ({"blocked_by": "RW-2"}, "Blocked by"),
        ({"state": "blocked", "blocked_by": "soon"}, "'soon'"),
        ({"source": "docs/a.md"}, "Source"),
        ({"ident": "KI-4"}, "ID is RW"),
    ],
)
def test_work_problems_name_the_broken_value(changes, fragment):
    """Each broken value is reported by its column."""
    assert any(fragment in problem for problem in _work(**changes).problems())


def test_blocked_by_a_sibling_and_an_external_reason_is_valid():
    """A sibling's ID and an external reason are both blocks."""
    entry = _work(state="blocked", blocked_by="sushiruntime RW-22, RW-3")
    assert entry.problems() == []
    assert entry.blocks() == ["sushiruntime RW-22", "RW-3"]
    assert _work(state="blocked", blocked_by="external: the vendor's fix").problems() == []


def test_with_value_refuses_the_id():
    """The ID cannot be set."""
    with pytest.raises(RowError):
        _work().with_value("ID", "RW-9")


def test_own_issue_needs_a_fix():
    """An issue of the repository's own names its fix or why there is none."""
    assert any("Fix is required" in p for p in _issue(fix="").problems())
    assert _issue(fix="none, chosen on purpose").problems() == []


def test_issue_of_the_toolchain_needs_no_fix():
    """An issue that is not the repository's own is never its to close."""
    assert _issue(origin="toolchain", fix="").problems() == []


def test_scheduled_fix_without_workaround_is_work_alone():
    """An own issue with no workaround and a fix in the backlog belongs to the backlog."""
    assert any("remaining work alone" in p for p in _issue(workaround="none").problems())


def test_sibling_origin_names_its_issue_and_is_cited():
    """A sibling's issue is written as its repository and ID, and counts as a citation."""
    entry = _issue(origin="sushiruntime KI-4", fix="")
    assert entry.problems() == []
    assert entry.cited() == ["sushiruntime KI-4"]
    assert any("Origin" in p for p in _issue(origin="sushiruntime").problems())
