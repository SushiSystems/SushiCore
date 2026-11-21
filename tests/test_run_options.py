# test_run_options.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The shared options of a `run` command that picks a program."""

import io

from datetime import date

import pytest
import typer
from typer.testing import CliRunner

from sushicore.aliases import Alias, AliasTable
from sushicore.run_options import list_all_option, old_pick_option, pick_option


pytestmark = pytest.mark.medium

K_REMOVED = date(2027, 3, 25)


class _Tty(io.StringIO):
    """A text stream that reports itself as a terminal."""

    def isatty(self) -> bool:
        """Returns True, as a terminal does."""
        return True


def _app(table: AliasTable) -> typer.Typer:
    """Returns an application whose one command declares the three shared options."""
    app = typer.Typer(name="sx", add_completion=False)

    @app.command("run")
    def run(
        pick: bool = pick_option(),
        sort: bool = old_pick_option(table, "sx run --sort"),
        list_all: bool = list_all_option(),
    ) -> None:
        """Run a program."""
        typer.echo(f"pick={pick or sort} all={list_all}")

    return app


def _table(stream: io.StringIO | None = None) -> AliasTable:
    """Returns a table that holds the old spelling `sx run --sort`, noticing on *stream*."""
    return AliasTable(
        "sx", (Alias("sx run --sort", "sx run --pick", K_REMOVED),), stream=stream)


def test_pick_and_all_set_their_flags():
    result = CliRunner().invoke(_app(_table()), ["--pick", "--all"])

    assert result.output == "pick=True all=True\n"


def test_neither_flag_given_leaves_both_off():
    assert CliRunner().invoke(_app(_table()), []).output == "pick=False all=False\n"


def test_the_old_flag_still_picks_and_is_left_out_of_the_help():
    app = _app(_table())

    assert CliRunner().invoke(app, ["--sort"]).output == "pick=True all=False\n"
    assert "--sort" not in CliRunner().invoke(app, ["--help"]).output


def test_the_old_flag_announces_its_replacement_once_to_a_terminal(monkeypatch):
    terminal = _Tty()
    monkeypatch.delenv("SX_NO_DEPRECATION_NOTICE", raising=False)
    table = _table(terminal)

    CliRunner().invoke(_app(table), ["--sort"])

    assert terminal.getvalue() == table.notice(table.alias_for("sx run --sort")) + "\n"


def test_an_old_option_may_answer_to_other_names():
    table = AliasTable("sx", (Alias("sx run --select", "sx run --pick", K_REMOVED),))
    app = typer.Typer(name="sx", add_completion=False)

    @app.command("run")
    def run(select: bool = old_pick_option(table, "sx run --select", "--select", "-s")) -> None:
        """Run a program."""
        typer.echo(f"select={select}")

    assert CliRunner().invoke(app, ["-s"]).output == "select=True\n"
