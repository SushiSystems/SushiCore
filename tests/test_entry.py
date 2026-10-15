# test_entry.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests `run`, which turns a CLI error into one line and an exit code."""

from datetime import date

import pytest

import typer

from sushicore.entry import run

from sushicore.errors import ConfigError, SushiCoreError



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



def test_run_turns_a_sushicore_error_into_one_line_and_exit_one():
    """The entry point reports a sushicore failure through the CLI's reporter and exits 1."""
    app = _app()

    @app.command("fail")
    def fail() -> None:
        """Raises the failure a broken configuration raises."""
        raise ConfigError("config.toml: bad value")

    reported: list[str] = []
    with pytest.raises(SystemExit) as caught:
        run(app, reported.append, argv=["fail"])
    assert caught.value.code == 1
    assert reported == ["config.toml: bad value"]



def test_run_falls_back_to_stderr_when_the_reporter_itself_fails(capsys):
    """A reporter that cannot be built still leaves the user one line on stderr."""
    app = _app()

    @app.command("fail")
    def fail() -> None:
        """Raises the failure a broken configuration raises."""
        raise ConfigError("config.toml: bad value")

    def broken(message: str) -> None:
        """Fails the way a console built from the same broken file fails."""
        raise ConfigError("cannot build the console")

    with pytest.raises(SystemExit) as caught:
        run(app, broken, argv=["fail"])
    assert caught.value.code == 1
    assert capsys.readouterr().err == "sx: config.toml: bad value\n"



def test_run_passes_a_normal_exit_and_other_errors_through():
    """A command's own exit code survives, and a bug is not disguised as a user error."""
    app = _app()

    @app.command("bug")
    def bug() -> None:
        """Raises what a programming error raises."""
        raise KeyError("oops")

    with pytest.raises(SystemExit) as caught:
        run(app, lambda message: None, argv=["build"])
    assert caught.value.code == 0
    with pytest.raises(KeyError):
        run(app, lambda message: None, argv=["bug"])
    assert issubclass(ConfigError, SushiCoreError)
