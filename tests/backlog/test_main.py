# test_main.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests `python -m sushicore.backlog`, the group for a repository with no CLI of its own."""

from __future__ import annotations

import io
import sys

import pytest

from sushicore.backlog import BacklogEditor
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


def test_main_shows_an_arrow_on_a_cp1252_console_without_raising(store, monkeypatch):
    """A title with an arrow reaches a console that cannot hold it without a UnicodeEncodeError."""
    entry = BacklogEditor(store).add_work(
        area="PHYSICS", priority="P2", title="Step → solve", done_when="it passes")
    console = io.TextIOWrapper(io.BytesIO(), encoding="cp1252")
    monkeypatch.setattr(sys, "stdout", console)
    assert main(["--root", str(store.root), "show", entry.ident]) == 0
