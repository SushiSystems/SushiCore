# commands.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The `backlog` command group, registered on a CLI from where its repository is.

The behaviour of each command is in `docs/reference/BACKLOG.md`. Each command is registered by its
own function in `command_read.py` or `command_write.py`; this file builds the groups and the
context they share and calls them in the order `--help` lists them.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Callable

from ..command_groups import K_BACKLOG
from . import command_read, command_write
from .command_context import CommandContext
from .history import GitHistory, Recorded
from .verification import GitVerification

if TYPE_CHECKING:
    import typer

K_HELP = "Read and change the backlog: remaining work and known issues, in docs/backlog/."


def register_backlog_commands(
    app: "typer.Typer",
    *,
    program: str,
    panel: str,
    project_root: Callable[[], Path],
    report: Callable[[str], None] = print,
    group_cls: type | None = None,
    unverified: Callable[[Path], frozenset[str] | None] = GitVerification().unverified,
    history: Callable[[Path], Recorded | None] = GitHistory().read,
) -> None:
    """Adds the `backlog` group to *app* under *panel*, with examples that name *program*.

    Args:
        app: The application to add the group to.
        project_root: Returns the repository root; called when a command runs.
        report: Prints one line of the result the way the CLI prints.
        unverified: Returns the IDs named after the verification stamp, or None without a stamp.
        history: Returns what git recorded of the backlog, or None when git cannot read it.
    """
    import typer

    def typer_app(help_text: str) -> typer.Typer:
        """Returns a group with the CLI's help class."""
        options: dict = {"help": help_text, "no_args_is_help": True, "rich_markup_mode": "rich"}
        if group_cls is not None:
            options["cls"] = group_cls
        return typer.Typer(**options)

    context = CommandContext(
        program=program, project_root=project_root, report=report, unverified=unverified,
        history=history)
    backlog_app = typer_app(K_HELP)
    add_app = typer_app("Add a work entry or a known issue.")
    area_app = typer_app("List or add the areas of the backlog.")

    command_read.register_list(backlog_app, context)
    command_read.register_show(backlog_app, context)
    command_read.register_next(backlog_app, context)
    command_read.register_here(backlog_app, context)
    command_read.register_decisions(backlog_app, context)
    command_read.register_flow(backlog_app, context)
    command_read.register_stale(backlog_app, context)
    command_write.register_add_work(add_app, context)
    command_write.register_add_issue(add_app, context)
    command_write.register_promote(backlog_app, context)
    command_write.register_set(backlog_app, context)
    command_write.register_close(backlog_app, context)
    command_write.register_pin(backlog_app, context)
    command_write.register_unpin(backlog_app, context)
    command_write.register_area_list(area_app, context)
    command_write.register_area_add(area_app, context)
    command_write.register_move(backlog_app, context)
    command_write.register_area_merge(area_app, context)
    command_write.register_renumber(backlog_app, context)
    command_read.register_check(backlog_app, context)

    backlog_app.add_typer(add_app, name="add")
    backlog_app.add_typer(area_app, name="area")
    app.add_typer(backlog_app, name=K_BACKLOG, rich_help_panel=panel)
