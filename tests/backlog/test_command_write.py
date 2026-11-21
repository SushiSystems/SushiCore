# test_command_write.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests the `backlog` commands that change the store: what each prints and what reaches the caller."""

from __future__ import annotations

import pytest

from sushicore.backlog import BacklogError

pytestmark = pytest.mark.medium


def test_add_work_prints_the_new_id(store, invoke):
    """`add work` prints the ID the entry took."""
    code, lines = invoke(store.root, "add", "work", "--area", "PHYSICS", "--priority", "P1",
                         "--title", "Fix the step", "--done-when", "it passes")
    assert (code, lines) == (0, ["RW-1"])


def test_close_prints_the_changelog_line(editor, store, invoke):
    """Closing prints the line to write."""
    editor.add_work(area="BUILD", priority="P2", title="Fix the gate", done_when="it passes")
    code, lines = invoke(store.root, "close", "RW-1", "--commit", "abc1234")
    assert code == 0 and lines[0].endswith("(RW-1, `abc1234`).")


def test_close_without_a_commit_prints_the_line_with_the_id_alone(editor, store, invoke):
    """`close` needs no commit, so it can run in the commit that does the work."""
    editor.add_work(area="BUILD", priority="P2", title="Fix the gate", done_when="it passes")
    code, lines = invoke(store.root, "close", "RW-1")
    assert code == 0 and lines[0].endswith("(RW-1).")


def test_renumber_says_it_rewrote_the_counters_and_the_index_when_no_id_is_shared(store, invoke):
    """With no shared ID the command still rewrites `ids.toml` and the index, and says so."""
    code, lines = invoke(store.root, "renumber")
    assert (code, lines[0], lines[-1].startswith("ids.toml and README.md")) == (0, "no ID is shared", True)


def test_a_refused_change_reaches_the_caller_as_the_backlog_error(store, invoke):
    """The group lets a BacklogError out, for the CLI's entry point to print."""
    with pytest.raises(BacklogError):
        invoke(store.root, "add", "work", "--area", "AUDIO", "--priority", "P1",
               "--title", "Fix it", "--done-when", "it passes")
