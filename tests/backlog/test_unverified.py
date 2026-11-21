# test_unverified.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests which IDs the commits after the verification stamp leave unverified."""

from __future__ import annotations

import pytest

from sushicore.backlog.unverified import Commit, unverified_ids

pytestmark = pytest.mark.small


def test_an_id_named_after_the_stamp_is_unverified():
    """A commit after the stamp that changes source and names RW-5 makes RW-5 unverified."""
    commit = Commit("feat: a thing\n\nBacklog: RW-5\n", ("source/a.py",))
    assert unverified_ids([commit]) == {"RW-5"}


def test_an_id_named_before_the_stamp_is_not_unverified():
    """Only the commits after the stamp are given; RW-4 sat in an older one and is absent."""
    after_stamp = [Commit("fix: a thing\n\nBacklog: RW-5, KI-2\n", ("source/a.py",))]
    assert "RW-4" not in unverified_ids(after_stamp)


def test_no_commit_after_the_stamp_marks_nothing():
    """Nothing committed since the stamp leaves nothing unverified."""
    assert unverified_ids([]) == frozenset()


def test_an_id_in_the_body_outside_the_backlog_line_is_not_named():
    """Only the `Backlog:` line counts."""
    commit = Commit("fix: RW-9 mentioned\n\nBacklog: none (docs)\n", ("source/a.py",))
    assert unverified_ids([commit]) == frozenset()


def test_a_commit_that_only_files_an_entry_marks_nothing():
    """A commit that changes the backlog and nothing else carries no work to verify."""
    commit = Commit("docs(backlog): file it\n\nBacklog: RW-7\n", ("docs/backlog/CODE.md", "docs/backlog/ids.toml"))
    assert unverified_ids([commit]) == frozenset()


def test_a_commit_that_changes_the_backlog_and_the_changelog_marks_nothing():
    """Closing an entry changes the backlog and the changelog only."""
    commit = Commit("chore(backlog): close it\n\nBacklog: RW-7\n", ("docs/backlog/CODE.md", "docs/reference/CHANGELOG.md"))
    assert unverified_ids([commit]) == frozenset()


def test_a_commit_that_changes_the_backlog_and_a_source_file_still_marks_its_entry():
    """One path outside the bookkeeping makes the commit work."""
    commit = Commit("feat: do it\n\nBacklog: RW-7\n", ("docs/backlog/CODE.md", "source/a.py"))
    assert unverified_ids([commit]) == {"RW-7"}


def test_a_commit_that_lists_no_path_counts_as_work():
    """An empty change set is not known to be bookkeeping."""
    assert unverified_ids([Commit("feat: do it\n\nBacklog: RW-7\n")]) == {"RW-7"}


def test_an_entry_of_a_sibling_marks_no_entry_here():
    """`Backlog: Other RW-5` names the sibling's RW-5, not this repository's."""
    commit = Commit("feat: do it\n\nBacklog: Other RW-5, RW-6\n", ("source/a.py",))
    assert unverified_ids([commit]) == {"RW-6"}


def test_an_id_inside_the_reason_of_none_marks_no_entry():
    """The reason of `none (...)` may cite an ID without serving it."""
    commit = Commit("feat: do it\n\nBacklog: none (RW-5 lives in the SushiSkills backlog)\n", ("source/a.py",))
    assert unverified_ids([commit]) == frozenset()
