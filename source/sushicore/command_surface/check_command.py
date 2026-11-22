# check_command.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Registers the shared ``check`` command; the CLI hands it the service that runs its checkers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Mapping, Sequence

from .check_service import CheckRequest, CheckService
from .command_function import command_function
from .command_parameter import CommandParameter
from .options import report_option, rule_option
from .panels import K_BUILD_PANEL
from .verbs import K_CHECK

if TYPE_CHECKING:
    import typer

K_CHECK_SUMMARY = "Run the checkers of the repository under tools/."


def register_check_command(
    app: "typer.Typer", service: CheckService, *, program: str, panel: str = K_BUILD_PANEL,
    parameters: Sequence[CommandParameter] = (), examples: Sequence[str] = (),
) -> None:
    """Add ``check`` to *app*: ``--report`` and ``--rule``.

    Args:
        app: The CLI's Typer application.
        service: Runs the checkers a request selects.
        program: The CLI's command, such as ``sd``, which the examples are written with.
        panel: The help panel the command is listed under.
        parameters: Options of the CLI's own, listed after the shared ones and handed over as ``extra``.
        examples: Example lines of the CLI's own, listed after the shared ones.
    """
    def act(ctx: Any, values: Mapping[str, Any], extra: Mapping[str, object]) -> int:
        """Builds the request from the parsed values and hands it to the service."""
        return service.check(CheckRequest(
            report=values["report"], rule=values["rule"], extra=extra, obj=ctx.obj))

    shared = (report_option(), rule_option())
    epilog = "\n".join((
        f"{program} check",
        f"{program} check --report  # Count the findings of each rule without failing",
        f"{program} check --rule <name>  # One rule",
        *examples,
    ))
    app.command(K_CHECK, rich_help_panel=panel, epilog=epilog)(
        command_function(shared, parameters, act, K_CHECK_SUMMARY))
