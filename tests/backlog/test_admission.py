# test_admission.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests the admission of a commit: the entries it changes and leaves open, and the entries it opens."""

from __future__ import annotations

import datetime

import pytest

from sushicore.backlog import IssueEntry, StagedChange, WorkEntry, admission_problems, entries_on
from sushicore.backlog.admission import covers

pytestmark = pytest.mark.small

K_DAY = datetime.date(2026, 11, 1)


def _work(ident: str, source: str = "`src/step.cpp`") -> WorkEntry:
    """Returns an open work entry on *source*."""
    return WorkEntry(ident, "P2", "open", f"Fix {ident}", "it passes", "", source, K_DAY)


def _change(*paths: str, parent: tuple[str, ...] = ("RW-1",), named: tuple[str, ...] = ()) -> StagedChange:
    """Returns a staged change of *paths* over a parent where *parent* is open."""
    return StagedChange(paths, frozenset(parent), frozenset(named))


@pytest.mark.parametrize(
    ("source", "path", "expected"),
    [
        ("`src/step.cpp`", "src/step.cpp", True),
        ("`src/physics`", "src/physics/step.cpp", True),
        ("`src/physics/`", "src/physics/step.cpp", True),
        ("`src/phys`", "src/physics/step.cpp", False),
        ("`src/step.cpp` §2", "src/step.cpp", True),
        ("", "src/step.cpp", False),
    ],
)
def test_covers_matches_the_path_or_a_folder_holding_it(source, path, expected):
    """A Source names a path when it is that path or one of its folders, never a name prefix."""
    assert covers(source, path) is expected


def test_entries_on_keeps_both_kinds_whose_source_covers_a_path():
    """`entries_on` reads the Source of work and issues alike."""
    issue = IssueEntry("KI-1", "own", "It drifts", "restart", "none, by design", "`src/step.cpp`", K_DAY)
    found = entries_on([_work("RW-1"), _work("RW-2", "`src/other.cpp`"), issue], ["src/step.cpp"])
    assert [entry.ident for entry in found] == ["RW-1", "KI-1"]


def test_admission_refuses_an_entry_whose_source_changed_and_that_the_line_does_not_name():
    """Changing the place of open work without closing or naming it is refused, with its ID and title."""
    problems = admission_problems([_work("RW-1")], _change("src/step.cpp"))
    assert problems == [
        "this commit changes the Source of RW-1 (Fix RW-1); close each one it finishes with "
        "`backlog close`, and name the rest in the `Backlog:` line",
    ]


def test_admission_accepts_an_entry_the_line_names():
    """Naming the entry in the `Backlog:` line says it was seen and stays open on purpose."""
    assert admission_problems([_work("RW-1")], _change("src/step.cpp", named=("RW-1",))) == []


def test_admission_accepts_an_entry_the_commit_closes():
    """A closed entry is gone from the store the commit leaves."""
    assert admission_problems([], _change("src/step.cpp")) == []


def test_admission_reads_no_path_under_docs():
    """A page under docs/ is a citation, not the place of the work."""
    assert admission_problems([_work("RW-1", "`docs/design/STEP.md`")], _change("docs/design/STEP.md")) == []


def test_admission_refuses_a_fourth_entry_opened_on_files_the_commit_changes():
    """The remainder of a change is finished or kept in its work folder's entry, not spread into the backlog."""
    opened = [_work(f"RW-{number}") for number in range(2, 6)]
    [problem] = admission_problems(opened, _change("src/step.cpp", parent=()))
    assert problem.startswith("this commit opens 4 entries on files it changes, RW-2 (Fix RW-2)")


def test_admission_accepts_three_entries_opened_on_files_the_commit_changes():
    """Three is the ceiling, so three pass."""
    opened = [_work(f"RW-{number}") for number in range(2, 5)]
    assert admission_problems(opened, _change("src/step.cpp", parent=())) == []


def test_admission_does_not_count_entries_opened_on_files_the_commit_leaves_alone():
    """A review that files what it found on other files opens findings, not a remainder."""
    opened = [_work(f"RW-{number}", "`src/other.cpp`") for number in range(2, 8)]
    assert admission_problems(opened, _change("src/step.cpp", parent=())) == []
