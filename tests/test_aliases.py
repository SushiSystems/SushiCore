# test_aliases.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests the alias table that keeps an old command spelling working until its date."""

import io

from datetime import date

import pytest

import typer

from typer.testing import CliRunner

from sushicore.aliases import Alias, AliasTable, UnknownAliasError

from sushicore.describe import catalogue



pytestmark = pytest.mark.medium



K_REMOVED = date(2027, 3, 25)



class _Tty(io.StringIO):
    """A text stream that reports itself as a terminal."""

    def isatty(self) -> bool:
        """Returns True, as a terminal does."""
        return True



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



def _table() -> AliasTable:
    """Returns a table with one dated and one permanent alias."""
    return AliasTable("sx", (Alias("sx doxygen", "sx docs", K_REMOVED), Alias("sx b", "sx build", None)))



def test_alias_notice_names_both_spellings_and_the_date():
    """The notice tells the user the new spelling and the last day of the old one."""
    table = _table()
    assert table.notice(table.alias_for("sx doxygen")) == (
        "sx: `sx doxygen` is now `sx docs`; the old spelling is removed after 2027-03-25.")



def test_alias_announces_once_to_a_terminal_only():
    """The notice is printed once per table, and never to a stream that is not a terminal."""
    table = _table()
    pipe, terminal = io.StringIO(), _Tty()
    table.announce(table.alias_for("sx doxygen"), stream=pipe)
    table.announce(table.alias_for("sx doxygen"), stream=terminal)
    table.announce(table.alias_for("sx doxygen"), stream=terminal)
    assert pipe.getvalue() == ""
    assert terminal.getvalue().count("\n") == 1



def test_alias_stays_silent_when_switched_off_or_permanent(monkeypatch):
    """The environment switch and a permanent alias both print nothing."""
    table = _table()
    terminal = _Tty()
    table.announce(table.alias_for("sx b"), stream=terminal)
    monkeypatch.setenv("SX_NO_DEPRECATION_NOTICE", "1")
    table.announce(table.alias_for("sx doxygen"), stream=terminal)
    assert terminal.getvalue() == ""



def test_alias_command_runs_the_new_command_and_is_hidden():
    """The old word runs the new command's callback and does not appear in the catalogue."""
    app = _app()
    table = AliasTable("sx", (Alias("sx make", "sx build", K_REMOVED),))
    build = next(info.callback for info in app.registered_commands if info.name == "build")
    table.command(app, "make", build, "sx make")
    assert CliRunner().invoke(app, ["make", "--clean"]).output == "built clean=True\n"
    names = [command["name"] for command in catalogue(app, distribution="sushicore")["commands"]]
    assert "make" not in names



def test_alias_table_reports_unknown_and_expired_rows():
    """An unknown spelling raises, and a row past its date is listed as expired."""
    table = _table()
    with pytest.raises(UnknownAliasError):
        table.alias_for("sx nothing")
    assert [alias.old for alias in table.expired(date(2027, 3, 26))] == ["sx doxygen"]
    assert table.expired(K_REMOVED) == []
