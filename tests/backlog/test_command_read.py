# test_command_read.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests the `backlog` commands that read the store: what each prints and its exit code."""

from __future__ import annotations

import datetime
import json

import pytest

from sushicore.backlog import Recorded
from sushicore.backlog.history import EntryLife, PathChange

pytestmark = pytest.mark.medium


def test_next_json_carries_the_columns_and_the_area(editor, store, invoke):
    """`next --json` prints the ready work with its columns and its area."""
    editor.add_work(area="PHYSICS", priority="P1", title="Fix the step", done_when="it passes")
    _, lines = invoke(store.root, "next", "--json")
    [entry] = json.loads(lines[0])
    assert (entry["ID"], entry["Area"]) == ("RW-1", "PHYSICS")


def test_show_json_carries_the_columns(editor, store, invoke):
    """`show --json` prints one entry with its columns."""
    editor.add_work(area="PHYSICS", priority="P1", title="Fix the step", done_when="it passes")
    _, lines = invoke(store.root, "show", "RW-1", "--json")
    assert json.loads(lines[0])["Title"] == "Fix the step"


def test_list_keeps_the_priorities_of_a_range(editor, store, invoke):
    """`--priority P0..P1` keeps the two highest priorities."""
    editor.add_work(area="BUILD", priority="P0", title="Fix the gate", done_when="it passes")
    editor.add_work(area="BUILD", priority="P2", title="Fix the gate", done_when="it passes")
    _, lines = invoke(store.root, "list", "--priority", "P0..P1")
    assert [line.split()[0] for line in lines] == ["RW-1"]


def test_list_keeps_the_entries_of_a_kind(editor, store, invoke):
    """`--kind issue` lists the known issues and no work."""
    editor.add_work(area="BUILD", priority="P0", title="Fix the gate", done_when="it passes")
    editor.add_issue(area="BUILD", origin="toolchain", symptom="The link fails", workaround="none")
    _, lines = invoke(store.root, "list", "--kind", "issue")
    assert [line.split()[0] for line in lines] == ["KI-1"]


def test_decisions_lists_the_entries_waiting_for_the_owner(editor, store, invoke):
    """Only the entries in the state `decision` are listed."""
    editor.add_work(area="BUILD", priority="P1", title="Choose the route", done_when="it is chosen", state="decision")
    editor.add_work(area="BUILD", priority="P1", title="Fix the gate", done_when="it passes")
    _, lines = invoke(store.root, "decisions")
    assert [line.split()[0] for line in lines] == ["RW-1"]


def test_check_exits_one_on_a_finding(store, invoke):
    """A fault is printed with its file and line and the exit code is 1."""
    (store.folder / "NOTES.md").write_text("# Notes\n", encoding="utf-8")
    code, lines = invoke(store.root, "check")
    assert code == 1
    assert lines[0].startswith("docs/backlog/NOTES.md:1:")


def test_here_lists_the_open_entries_whose_source_covers_a_path(editor, store, invoke):
    """An entry on the folder and one on the file are listed; one on another file is not."""
    editor.add_work(area="PHYSICS", priority="P2", title="Fix the step", done_when="it passes",
                    source="modules/physics")
    editor.add_work(area="PHYSICS", priority="P2", title="Fix the gate", done_when="it passes",
                    source="docs/design")
    _, lines = invoke(store.root, "here", "modules/physics/step.cpp")
    assert [line.split()[0] for line in lines] == ["RW-1"]


def test_here_says_so_when_no_entry_names_the_paths(editor, store, invoke):
    """An empty answer is a line, not silence."""
    _, lines = invoke(store.root, "here", "modules/physics/step.cpp")
    assert lines == ["no open entry names these paths"]


def test_flow_prints_the_measures_git_recorded(store, invoke):
    """The window's opened and closed work comes from the history reader, dated against the real clock."""
    day = datetime.date.today()
    recorded = Recorded([EntryLife("RW-1", day, "`src/a.cpp`", closed=day)], [])
    _, lines = invoke(store.root, "flow", "--json", history=lambda _root: recorded)
    payload = json.loads(lines[0])
    assert (payload["opened"], payload["closed"], payload["closed_same_day"]) == (1, 1, 1)


def test_flow_exits_one_when_git_cannot_read_the_history(store, invoke):
    """No history is a finding, not an empty flow."""
    code, lines = invoke(store.root, "flow", history=lambda _root: None)
    assert (code, lines) == (1, ["git cannot read the history of docs/backlog/"])


def test_stale_lists_old_work_with_its_later_commits(editor, store, invoke):
    """Work the fixture opened a month before the real clock is past a triage age of 14 days."""
    editor.add_work(area="PHYSICS", priority="P2", title="Fix the step", done_when="it passes",
                    source="modules/physics")
    later = store.today() + datetime.timedelta(days=1)
    recorded = Recorded([], [PathChange(later, ("modules/physics/step.cpp",))])
    _, lines = invoke(store.root, "stale", "--days", "14", history=lambda _root: recorded)
    assert (lines[0].split()[0], lines[0].endswith("(1 later commits to its Source)")) == ("RW-1", True)
