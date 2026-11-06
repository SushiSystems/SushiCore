# test_commands.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests the `backlog` group a CLI registers: what each command prints and its exit code."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import typer
from typer.testing import CliRunner

from sushicore.backlog import BacklogError, register_backlog_commands
from sushicore.console_memory import RecordingConsole

pytestmark = pytest.mark.medium


def _invoke(root: Path, *arguments: str) -> tuple[int, list[str]]:
    """Runs one command of an application named `sx` and returns its code and its lines."""
    console = RecordingConsole()
    app = typer.Typer(name="sx", no_args_is_help=True, add_completion=False)

    @app.command("build")
    def build() -> None:
        """Build."""

    register_backlog_commands(
        app, program="sx", panel="Project", project_root=lambda: root, report=console.info,
    )
    result = CliRunner().invoke(app, ["backlog", *arguments])
    if result.exception and not isinstance(result.exception, SystemExit):
        raise result.exception
    return result.exit_code, console.texts("info")


def test_add_work_prints_the_new_id(store):
    """`add work` prints the ID the entry took."""
    code, lines = _invoke(store.root, "add", "work", "--area", "PHYSICS", "--priority", "P1",
                          "--title", "Fix the step", "--done-when", "it passes")
    assert (code, lines) == (0, ["RW-1"])


def test_next_json_carries_the_columns_and_the_area(editor, store):
    """`next --json` prints the ready work with its columns and its area."""
    editor.add_work(area="PHYSICS", priority="P1", title="Fix the step", done_when="it passes")
    _, lines = _invoke(store.root, "next", "--json")
    [entry] = json.loads(lines[0])
    assert (entry["ID"], entry["Area"]) == ("RW-1", "PHYSICS")


def test_show_json_carries_the_columns(editor, store):
    """`show --json` prints one entry with its columns."""
    editor.add_work(area="PHYSICS", priority="P1", title="Fix the step", done_when="it passes")
    _, lines = _invoke(store.root, "show", "RW-1", "--json")
    assert json.loads(lines[0])["Title"] == "Fix the step"


def test_list_keeps_the_priorities_of_a_range(editor, store):
    """`--priority P0..P1` keeps the two highest priorities."""
    editor.add_work(area="BUILD", priority="P0", title="Fix the gate", done_when="it passes")
    editor.add_work(area="BUILD", priority="P2", title="Fix the gate", done_when="it passes")
    _, lines = _invoke(store.root, "list", "--priority", "P0..P1")
    assert [line.split()[0] for line in lines] == ["RW-1"]


def test_list_keeps_the_entries_of_a_kind(editor, store):
    """`--kind issue` lists the known issues and no work."""
    editor.add_work(area="BUILD", priority="P0", title="Fix the gate", done_when="it passes")
    editor.add_issue(area="BUILD", origin="toolchain", symptom="The link fails", workaround="none")
    _, lines = _invoke(store.root, "list", "--kind", "issue")
    assert [line.split()[0] for line in lines] == ["KI-1"]


def test_close_prints_the_changelog_line(editor, store):
    """Closing prints the line to write."""
    editor.add_work(area="BUILD", priority="P2", title="Fix the gate", done_when="it passes")
    code, lines = _invoke(store.root, "close", "RW-1", "--commit", "abc1234")
    assert code == 0 and lines[0].endswith("(RW-1, `abc1234`).")


def test_check_exits_one_on_a_finding(store):
    """A fault is printed with its file and line and the exit code is 1."""
    (store.folder / "NOTES.md").write_text("# Notes\n", encoding="utf-8")
    code, lines = _invoke(store.root, "check")
    assert code == 1
    assert lines[0].startswith("docs/backlog/NOTES.md:1:")


def test_a_refused_change_reaches_the_caller_as_the_backlog_error(store):
    """The group lets a BacklogError out, for the CLI's entry point to print."""
    with pytest.raises(BacklogError):
        _invoke(store.root, "add", "work", "--area", "AUDIO", "--priority", "P1",
                "--title", "Fix it", "--done-when", "it passes")
