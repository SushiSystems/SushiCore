# test_entry.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests `run`, which turns a CLI error into one line and an exit code."""

import io

import pytest

import typer

from sushicore.cli_console import LazyConsole
from sushicore.console import Console
from sushicore.entry import run
from sushicore.errors import ConfigError
from sushicore.icons import IconSet
from sushicore.renderer import PlainRenderer
from sushicore.theme import Theme


def _fail() -> None:
    """Raises the failure a broken configuration raises."""
    raise ConfigError("config.toml: bad value")


def _bug() -> None:
    """Raises what a programming error raises."""
    raise KeyError("oops")


def _build() -> None:
    """Returns normally, as a command that succeeds does."""
    typer.echo("built")


def _app() -> typer.Typer:
    """Returns an application named `sx` with a command that succeeds and two that raise."""
    app = typer.Typer(name="sx", help="Builds things.", no_args_is_help=True, add_completion=False)
    app.command("build")(_build)
    app.command("fail")(_fail)
    app.command("bug")(_bug)
    return app


@pytest.mark.small
def test_run_turns_a_sushicore_error_into_one_line_and_exit_one():
    """The entry point reports a sushicore failure through the CLI's reporter and exits 1."""
    stream = io.StringIO()
    console = Console(PlainRenderer(stream), Theme(), IconSet(error="E"))
    with pytest.raises(SystemExit) as caught:
        run(_app(), console.error, argv=["fail"])
    assert caught.value.code == 1
    assert stream.getvalue() == "E config.toml: bad value\n"


@pytest.mark.medium
def test_run_falls_back_to_stderr_when_the_reporter_itself_fails(tmp_path, capsys):
    """A console built from the same broken file still leaves the user one line on stderr."""
    (tmp_path / "config.toml").write_text("this is [not toml", encoding="utf-8")
    lazy = LazyConsole(lambda: tmp_path)
    with pytest.raises(SystemExit) as caught:
        run(_app(), lambda message: lazy.attribute("error")(message), argv=["fail"])
    assert caught.value.code == 1
    assert capsys.readouterr().err == "sx: config.toml: bad value\n"


@pytest.mark.small
def test_run_exits_zero_after_a_command_that_succeeds():
    """A command that returns normally leaves the process exit code 0."""
    with pytest.raises(SystemExit) as caught:
        run(_app(), lambda message: None, argv=["build"])
    assert caught.value.code == 0


@pytest.mark.small
def test_run_does_not_disguise_a_bug_as_a_user_error():
    """An error that is not a sushicore failure stays a traceback."""
    with pytest.raises(KeyError):
        run(_app(), lambda message: None, argv=["bug"])
