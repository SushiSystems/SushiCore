# test_commands.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests the `backlog` group a CLI registers: what each command prints and its exit code."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import typer
from typer.testing import CliRunner

from sushicore.backlog import register_backlog_commands

pytestmark = pytest.mark.medium


def _invoke(root: Path, *arguments: str) -> tuple[int, list[str]]:
    """Runs one command of an application named `sx` and returns its code and its lines."""
    reported: list[str] = []
    app = typer.Typer(name="sx", no_args_is_help=True, add_completion=False)

    @app.command("build")
    def build() -> None:
        """Build."""

    register_backlog_commands(
        app, program="sx", panel="Project", project_root=lambda: root, report=reported.append,
    )
    result = CliRunner().invoke(app, ["backlog", *arguments])
    if result.exception and not isinstance(result.exception, SystemExit):
        raise result.exception
    return result.exit_code, reported


def test_an_agent_adds_work_and_reads_it_back_as_json(store):
    """`add work` prints the ID; `next --json` and `show --json` carry the columns."""
    root = store.root
    code, lines = _invoke(root, "add", "work", "--area", "PHYSICS", "--priority", "P1",
                          "--title", "Fix the step", "--done-when", "it passes")
    assert (code, lines) == (0, ["RW-1"])
    _, lines = _invoke(root, "next", "--json")
    payload = json.loads(lines[0])
    assert payload[0]["ID"] == "RW-1" and payload[0]["Area"] == "PHYSICS"
    _, lines = _invoke(root, "show", "RW-1", "--json")
    assert json.loads(lines[0])["Title"] == "Fix the step"


def test_list_filters_by_priority_range_and_kind(store):
    """`--priority P0..P1` keeps the two highest priorities."""
    root = store.root
    for priority in ("P0", "P2"):
        _invoke(root, "add", "work", "--area", "BUILD", "--priority", priority,
                "--title", "Fix the gate", "--done-when", "it passes")
    _invoke(root, "add", "issue", "--area", "BUILD", "--origin", "toolchain",
            "--symptom", "The link fails", "--workaround", "none")
    _, lines = _invoke(root, "list", "--priority", "P0..P1")
    assert [line.split()[0] for line in lines] == ["RW-1"]
    _, lines = _invoke(root, "list", "--kind", "issue")
    assert [line.split()[0] for line in lines] == ["KI-1"]


def test_close_prints_the_changelog_line_and_check_stays_clean(store):
    """Closing prints the line to write; the store still checks clean."""
    root = store.root
    _invoke(root, "add", "work", "--area", "BUILD", "--priority", "P2",
            "--title", "Fix the gate", "--done-when", "it passes")
    code, lines = _invoke(root, "close", "RW-1", "--commit", "abc1234")
    assert code == 0 and lines[0].endswith("(RW-1, `abc1234`).")
    assert _invoke(root, "check") == (0, ["clean"])


def test_check_exits_one_on_a_finding(store):
    """A fault is printed with its file and line and the exit code is 1."""
    (store.folder / "NOTES.md").write_text("# Notes\n", encoding="utf-8")
    code, lines = _invoke(store.root, "check")
    assert code == 1
    assert lines[0].startswith("docs/backlog/NOTES.md:1:")


def test_a_refused_change_reaches_the_caller_as_the_backlog_error(store):
    """The CLI's entry point prints a BacklogError as one line."""
    from sushicore.backlog import BacklogError

    with pytest.raises(BacklogError):
        _invoke(store.root, "add", "work", "--area", "AUDIO", "--priority", "P1",
                "--title", "Fix it", "--done-when", "it passes")
