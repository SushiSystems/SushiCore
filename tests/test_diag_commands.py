# test_diag_commands.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests the diagnostic commands a CLI registers."""

from datetime import date

import pytest

import typer

from typer.testing import CliRunner

from sushicore.diag_commands import register_diagnostic_commands



pytestmark = pytest.mark.medium



K_REMOVED = date(2027, 3, 25)



class _Diagnostics:
    """Records which diagnostic was asked for."""

    def __init__(self) -> None:
        self.calls: list[tuple] = []

    def config_show(self) -> int:
        """Records the call and reports success."""
        self.calls.append(("config",))
        return 0

    def env_dump(self, show_all: bool = False) -> int:
        """Records the call and reports the failure code 3."""
        self.calls.append(("env", show_all))
        return 3



def _app() -> typer.Typer:
    """Returns an application named `sx` with one command and one hidden command."""
    app = typer.Typer(name="sx", help="Builds things.", no_args_is_help=True, add_completion=False)

    @app.command("build")
    def build(clean: bool = typer.Option(False, "--clean", help="Start over.")) -> None:
        """Configure and build.

        A second paragraph the catalogue leaves out.
        """
        typer.echo(f"built clean={clean}")

    @app.command("old-build", hidden=True)
    def old_build() -> None:
        """The old spelling."""

    return app



def test_diagnostic_commands_delegate_and_return_the_code():
    """config and env call the diagnostics object and exit with what it returns."""
    app = _app()
    diagnostics = _Diagnostics()
    register_diagnostic_commands(app, diagnostics, program="sx", panel="Diagnostics")
    runner = CliRunner()
    assert runner.invoke(app, ["config"]).exit_code == 0
    assert runner.invoke(app, ["env", "--all"]).exit_code == 3
    assert runner.invoke(app, ["env", "-a"]).exit_code == 3
    assert diagnostics.calls == [("config",), ("env", True), ("env", True)]



def test_diagnostic_commands_can_leave_env_to_the_cli():
    """A CLI whose env takes its own flags registers config alone."""
    app = _app()
    register_diagnostic_commands(app, _Diagnostics(), program="sx", panel="Diagnostics", env=False)
    assert CliRunner().invoke(app, ["env"]).exit_code == 2
