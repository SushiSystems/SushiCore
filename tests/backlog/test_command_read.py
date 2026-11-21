# test_command_read.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests the `backlog` commands that read the store: what each prints and its exit code."""

from __future__ import annotations

import json

import pytest

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
