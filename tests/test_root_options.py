# test_root_options.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests the root options every Sushi CLI takes: the version line and the help."""

from datetime import date

import pytest

import typer

from typer.testing import CliRunner

from sushicore.root_options import register_root_options, version_line



pytestmark = pytest.mark.medium



K_REMOVED = date(2027, 3, 25)



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



def test_version_prints_the_distribution_and_exits_zero():
    """--version prints one line naming the distribution and runs no command."""
    app = _app()
    register_root_options(app, distribution="sushicore")
    result = CliRunner().invoke(app, ["--version"])
    assert result.exit_code == 0
    assert result.output.strip() == version_line("sushicore")
    assert result.output.startswith("sushicore ")



def test_version_of_an_unknown_distribution_reads_unknown():
    """A distribution that is not installed reports `unknown`, not a traceback."""
    assert version_line("no-such-distribution-xyz") == "no-such-distribution-xyz unknown"



def test_version_lines_can_be_supplied_by_the_cli():
    """A CLI that knows more than its version prints its own lines."""
    app = _app()
    register_root_options(app, distribution="sushicore", version_lines=lambda: ["sx 1", "root /x"])
    assert CliRunner().invoke(app, ["--version"]).output == "sx 1\nroot /x\n"



def test_root_options_keep_the_help_and_the_commands():
    """Registering the root options changes neither the help text nor a command's behaviour."""
    app = _app()
    register_root_options(app, distribution="sushicore")
    runner = CliRunner()
    assert "Builds things." in runner.invoke(app, ["--help"]).output
    assert runner.invoke(app, ["build", "--clean"]).output == "built clean=True\n"
