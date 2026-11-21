# test_command_context.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests what every command shares: how an entry prints and which entries carry the unverified mark."""

from __future__ import annotations

import datetime
from pathlib import Path

import pytest

from sushicore.backlog import IssueEntry, WorkEntry
from sushicore.backlog.command_context import entry_line, is_unverified, shown_path

K_DAY = datetime.date(2026, 10, 28)


def _work(state: str = "open") -> WorkEntry:
    """Returns a work entry opened on the day itself."""
    return WorkEntry("RW-1", "P2", state, "Fix the step", "it passes", "", "", K_DAY)


@pytest.mark.small
def test_a_work_entry_prints_its_priority_state_age_and_title():
    """The line of a work entry is what `list` and `next` show."""
    assert entry_line(_work(), K_DAY) == "RW-1 P2 open 0d: Fix the step"


@pytest.mark.small
def test_a_known_issue_prints_its_origin_and_symptom():
    """The line of an issue has no priority or age."""
    issue = IssueEntry("KI-4", "toolchain", "The link fails", "none", "", "", K_DAY)
    assert entry_line(issue, K_DAY) == "KI-4 toolchain: The link fails"


@pytest.mark.small
@pytest.mark.parametrize("state, named, expected", [
    ("open", True, True),
    ("open", False, False),
    ("blocked", True, False),
])
def test_only_an_open_work_entry_named_after_the_stamp_is_unverified(state, named, expected):
    """A blocked entry, or one no commit names, carries no mark."""
    ids = frozenset({"RW-1"}) if named else frozenset()
    assert is_unverified(_work(state), ids) is expected


@pytest.mark.small
def test_a_path_under_the_root_is_shown_from_it_and_one_outside_is_shown_whole():
    """A fault names a file from the repository root when it can."""
    root = Path("repo")
    assert (shown_path(root / "docs" / "a.md", root), shown_path(Path("other") / "b.md", root)) == (
        "docs/a.md", str(Path("other") / "b.md"))


@pytest.mark.medium
def test_list_marks_an_open_entry_named_after_the_stamp(editor, store, invoke):
    """An open entry that a commit after the stamp names is printed as unverified."""
    editor.add_work(area="BUILD", priority="P2", title="Fix the gate", done_when="it passes")
    editor.add_work(area="BUILD", priority="P2", title="Fix the link", done_when="it passes")
    _, lines = invoke(store.root, "list", unverified=lambda _root: frozenset({"RW-2"}))
    assert [line.endswith(" unverified") for line in lines] == [False, True]


@pytest.mark.medium
def test_list_marks_nothing_and_says_so_without_a_stamp(editor, store, invoke):
    """Without a stamp no entry is marked and one line says no stamp exists."""
    editor.add_work(area="BUILD", priority="P2", title="Fix the gate", done_when="it passes")
    _, lines = invoke(store.root, "list", unverified=lambda _root: None)
    assert [line.endswith(" unverified") for line in lines] == [False, False]
    assert lines[-1].startswith("no verification stamp exists")


@pytest.mark.medium
def test_next_marks_an_open_entry_named_after_the_stamp(editor, store, invoke):
    """`next` prints the same mark."""
    editor.add_work(area="BUILD", priority="P2", title="Fix the gate", done_when="it passes")
    _, lines = invoke(store.root, "next", unverified=lambda _root: frozenset({"RW-1"}))
    assert lines[0].endswith(" unverified")
