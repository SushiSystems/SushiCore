# diag_commands.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""The ``config`` and ``env`` commands, registered on a CLI from its diagnostics object.

Six CLIs declared the same two commands around :class:`sushicore.diag.Diagnostics`. This is
the one declaration; a CLI passes its diagnostics and the help panel the commands sit in.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    import typer


class DiagnosticsLike(Protocol):
    """The two reports the commands print."""

    def config_show(self) -> int: ...
    def env_dump(self, show_all: bool = ...) -> int: ...


def register_diagnostic_commands(
    app: "typer.Typer", diagnostics: DiagnosticsLike, *, program: str, panel: str,
    env: bool = True,
) -> None:
    """Adds ``config`` and, unless *env* is False, ``env`` to *app*.

    Args:
        app: The application to add the commands to.
        diagnostics: The object that prints the two reports and returns their exit codes.
        program: The command the user types, for the examples.
        panel: The help panel the commands are listed under.
        env: False for a CLI whose ``env`` takes flags of its own and is declared there.
    """
    import typer

    @app.command("config", rich_help_panel=panel, epilog=f"{program} config")
    def config() -> None:
        """Print the resolved config and where each value came from."""
        raise typer.Exit(diagnostics.config_show())

    if not env:
        return

    @app.command(
        "env", rich_help_panel=panel,
        epilog=f"{program} env\n"
               f"{program} env --all  # Show every variable, not just build-relevant ones",
    )
    def env_command(
        show_all: bool = typer.Option(
            False, "--all", "-a", help="Show every variable, not just build-relevant ones."),
    ) -> None:
        """Print the environment cmake/ctest/run subprocesses execute under."""
        raise typer.Exit(diagnostics.env_dump(show_all=show_all))
