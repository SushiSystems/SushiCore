# test_main.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests `python -m sushicore.backlog`, the group for a repository with no CLI of its own."""

from __future__ import annotations

import pytest

from sushicore.backlog.__main__ import main

pytestmark = pytest.mark.medium


def test_main_runs_a_command_on_the_root_it_is_given(store, capsys):
    """`--root` names the repository; the exit code is the command's."""
    assert main(["--root", str(store.root), "area", "list"]) == 0
    assert capsys.readouterr().out.split() == ["BUILD", "PHYSICS"]


def test_main_prints_a_backlog_error_as_one_line(store, capsys):
    """A refused change exits 1 with one line on standard error."""
    code = main(["--root", str(store.root), "show", "RW-1"])
    assert code == 1
    assert capsys.readouterr().err.strip() == "python -m sushicore.backlog: RW-1 names no open entry"


def test_main_returns_the_check_code(store, capsys):
    """A finding exits 1."""
    (store.folder / "NOTES.md").write_text("# Notes\n", encoding="utf-8")
    assert main(["--root", str(store.root), "check"]) == 1
