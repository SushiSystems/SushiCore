# test_aliases.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests the alias table that keeps an old command spelling working until its date."""

import io
import sys

from datetime import date

import pytest

import typer

from typer.testing import CliRunner

from sushicore.aliases import Alias, AliasTable, UnknownAliasError



K_REMOVED = date(2027, 3, 25)

K_SWITCH_OFF = {"SX_NO_DEPRECATION_NOTICE": "1"}



class _Tty(io.StringIO):
    """A text stream that reports itself as a terminal."""

    def isatty(self) -> bool:
        """Returns True, as a terminal does."""
        return True



def _app() -> typer.Typer:
    """Returns an application named `sx` with one command."""
    app = typer.Typer(name="sx", help="Builds things.", no_args_is_help=True, add_completion=False)

    @app.command("build")
    def build(clean: bool = typer.Option(False, "--clean", help="Start over.")) -> None:
        """Configure and build."""
        typer.echo(f"built clean={clean}")

    return app



def _table() -> AliasTable:
    """Returns a table with one dated and one permanent alias."""
    return AliasTable("sx", (Alias("sx doxygen", "sx docs", K_REMOVED), Alias("sx b", "sx build", None)))



@pytest.mark.small
def test_alias_notice_names_both_spellings_and_the_date():
    """The notice tells the user the new spelling and the last day of the old one."""
    table = _table()
    assert table.notice(table.alias_for("sx doxygen")) == (
        "sx: `sx doxygen` is now `sx docs`; the old spelling is removed after 2027-03-25.")



@pytest.mark.small
def test_alias_announces_once_to_a_terminal_only():
    """The notice is printed once per table, and never to a stream that is not a terminal."""
    table = _table()
    pipe, terminal = io.StringIO(), _Tty()
    table.announce(table.alias_for("sx doxygen"), stream=pipe, environ={})
    table.announce(table.alias_for("sx doxygen"), stream=terminal, environ={})
    table.announce(table.alias_for("sx doxygen"), stream=terminal, environ={})
    assert pipe.getvalue() == ""
    assert terminal.getvalue().count("\n") == 1



@pytest.mark.small
def test_alias_stays_silent_for_a_permanent_alias():
    """A permanent alias prints nothing."""
    table = _table()
    terminal = _Tty()
    table.announce(table.alias_for("sx b"), stream=terminal, environ={})
    assert terminal.getvalue() == ""



@pytest.mark.small
def test_alias_stays_silent_when_the_switch_is_on():
    """The environment switch silences a dated alias."""
    table = _table()
    terminal = _Tty()
    table.announce(table.alias_for("sx doxygen"), stream=terminal, environ=K_SWITCH_OFF)
    assert terminal.getvalue() == ""



@pytest.mark.medium
def test_alias_command_runs_the_new_command():
    """The old word runs the new command's callback."""
    app = _app()
    table = AliasTable("sx", (Alias("sx make", "sx build", K_REMOVED),))
    build = next(info.callback for info in app.registered_commands if info.name == "build")
    table.command(app, "make", build, "sx make")
    assert CliRunner().invoke(app, ["make", "--clean"]).output == "built clean=True\n"



@pytest.mark.medium
def test_deprecated_announces_the_alias_once_and_calls_the_callback_unchanged(monkeypatch):
    """The wrapper prints the notice on the first call only and returns the callback's result."""
    terminal = _Tty()
    monkeypatch.setattr(sys, "stderr", terminal)
    monkeypatch.delenv("SX_NO_DEPRECATION_NOTICE", raising=False)
    table = _table()
    wrapped = table.deprecated(lambda value: value * 2, "sx doxygen")
    assert (wrapped(2), wrapped(3)) == (4, 6)
    assert terminal.getvalue() == table.notice(table.alias_for("sx doxygen")) + "\n"



@pytest.mark.small
def test_alias_table_raises_for_an_unknown_spelling():
    """An unknown spelling raises."""
    with pytest.raises(UnknownAliasError):
        _table().alias_for("sx nothing")



@pytest.mark.small
def test_alias_table_lists_the_rows_past_their_date_as_expired():
    """A row past its date is listed as expired, and a row on its last day is not."""
    table = _table()
    assert [alias.old for alias in table.expired(date(2027, 3, 26))] == ["sx doxygen"]
    assert table.expired(K_REMOVED) == []


@pytest.mark.small
def test_a_table_built_with_a_stream_announces_there_through_deprecated():
    stream = _Tty()
    alias = Alias("sx doxygen", "sx docs", K_REMOVED)
    table = AliasTable("sx", (alias,), stream=stream, environ={})
    assert table.deprecated(lambda: 7, "sx doxygen")() == 7
    assert stream.getvalue() == table.notice(alias) + "\n"
