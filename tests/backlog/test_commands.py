# test_commands.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests the `backlog` group a CLI registers: which commands it holds and where it sits."""

from __future__ import annotations

import pytest
import typer

from sushicore.backlog import register_backlog_commands

pytestmark = pytest.mark.medium


def test_the_group_holds_every_command_in_the_order_help_lists_them(store):
    """Each command's registering function is called once, and the groups come last."""
    app = typer.Typer(name="sx", no_args_is_help=True, add_completion=False)
    register_backlog_commands(app, program="sx", panel="Project", project_root=lambda: store.root)
    group = typer.main.get_command(app).commands["backlog"]
    assert list(group.commands) == [
        "list", "show", "next", "decisions", "promote", "set", "close", "pin", "unpin", "move",
        "renumber", "import", "check", "add", "area",
    ]


def test_the_group_nests_the_add_and_area_commands(store):
    """`add` holds `work` and `issue`; `area` holds `list`, `add` and `merge`."""
    app = typer.Typer(name="sx", no_args_is_help=True, add_completion=False)
    register_backlog_commands(app, program="sx", panel="Project", project_root=lambda: store.root)
    group = typer.main.get_command(app).commands["backlog"]
    assert (list(group.commands["add"].commands), list(group.commands["area"].commands)) == (
        ["work", "issue"], ["list", "add", "merge"])
