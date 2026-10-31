# test_commands.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests that every CLI which registers the shared test command declares the same options."""

from pathlib import Path

import pytest
import typer
from typer.testing import CliRunner

from sushicore.profile import ModuleProfile
from sushicore.testing import ModuleTests, register_test_command

pytestmark = pytest.mark.medium


def _app(calls):
    profile = ModuleProfile(name="sushitrack", program="st", env_prefix="ST", root_marker="m")

    class _Console:
        def error(self, text):
            calls.append(text)

    module = ModuleTests(profile=profile, project_root=lambda: Path("."), console=_Console,
                         build_tree=lambda: Path("."), run_ctest=lambda tree, **keywords: 0,
                         run=lambda command, cwd: 0)
    app = typer.Typer()

    @app.callback()
    def _root():
        """Test app."""

    register_test_command(app, module)
    return app


def test_the_command_declares_the_same_options_in_every_cli():
    command = typer.main.get_command(_app([])).commands["test"]
    names = sorted(name for parameter in command.params for name in parameter.opts)
    assert names == ["--all", "--cli", "--filter", "--jobs", "--label", "--repeat", "--sanitize",
                     "-f", "-j", "-l", "-r"]


def test_the_options_a_module_cannot_serve_are_hidden():
    command = typer.main.get_command(_app([])).commands["test"]
    hidden = {parameter.opts[0] for parameter in command.params if parameter.hidden}
    assert hidden == {"--cli", "--sanitize"}


def test_asking_for_large_without_a_filter_exits_with_the_usage_code():
    said = []
    result = CliRunner().invoke(_app(said), ["test", "--label", "large"])
    assert result.exit_code == 2 and said
