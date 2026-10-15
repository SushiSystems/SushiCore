# test_describe.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests the catalogue `describe` prints of a CLI's commands."""

import json

from datetime import date

import pytest

import typer

from typer.testing import CliRunner

from sushicore.describe import K_CONTRACT_VERSION, catalogue

from sushicore.root_options import register_root_options



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



def test_describe_prints_the_catalogue_without_hidden_commands():
    """--describe prints the catalogue as JSON and leaves hidden spellings out."""
    app = _app()
    register_root_options(app, distribution="sushicore")
    result = CliRunner().invoke(app, ["--describe"])
    assert result.exit_code == 0
    document = json.loads(result.output)
    assert document["program"] == "sx"
    assert document["contract"] == K_CONTRACT_VERSION
    assert [command["name"] for command in document["commands"]] == ["build"]
    assert document["commands"][0]["help"] == "Configure and build."
    assert document["commands"][0]["params"][0]["flags"] == ["--clean"]



def test_catalogue_carries_applies_to():
    """The catalogue repeats the presence list a caller gives it on every command."""
    document = catalogue(_app(), distribution="sushicore", applies_to=("cloned",))
    assert document["commands"][0]["applies_to"] == ["cloned"]



def test_catalogue_lists_a_group_that_runs_bare_beside_its_children():
    """A group that runs without a subcommand is a command; one that shows help is not."""
    app = _app()
    docs = typer.Typer(help="Build the reference.")

    @docs.callback(invoke_without_command=True)
    def docs_root() -> None:
        """Runs when no subcommand is given."""

    @docs.command("bundle")
    def bundle() -> None:
        """Bundle the pages."""

    container = typer.Typer(help="Containers.", no_args_is_help=True)

    @container.command("run")
    def container_run() -> None:
        """Start the container."""

    app.add_typer(docs, name="docs")
    app.add_typer(container, name="container")
    commands = catalogue(app, distribution="sushicore")["commands"]
    assert [command["name"] for command in commands] == [
        "build", "container run", "docs", "docs bundle",
    ]
    assert commands[2]["help"] == "Build the reference."
    assert commands[2]["params"] == []
