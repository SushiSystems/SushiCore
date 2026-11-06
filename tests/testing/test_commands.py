# test_commands.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests that every CLI which registers the shared test command declares the same options."""

from pathlib import Path

import pytest
import typer

from sushicore.console_memory import RecordingConsole
from sushicore.profile import ModuleProfile
from sushicore.testing import ModuleTests, register_test_command

pytestmark = pytest.mark.small


def _app():
    profile = ModuleProfile(name="sushitrack", program="st", env_prefix="ST", root_marker="m")
    console = RecordingConsole()
    module = ModuleTests(profile=profile, project_root=lambda: Path("."), console=lambda: console,
                         build_tree=lambda: Path("."), run_ctest=lambda tree, **keywords: 0,
                         run=lambda command, cwd: 0)
    app = typer.Typer()

    @app.callback()
    def _root():
        """Test app."""

    register_test_command(app, module)
    return app


def test_the_command_declares_its_own_options_beside_the_shared_ones():
    command = typer.main.get_command(_app()).commands["test"]
    names = {name for parameter in command.params for name in parameter.opts}
    shared = {"--all", "--filter", "--jobs", "--label", "--repeat", "-f", "-j", "-l", "-r"}
    assert names - shared == {"--cli", "--sanitize", "--seed", "--shuffle"}


def test_the_options_a_module_cannot_serve_are_hidden():
    command = typer.main.get_command(_app()).commands["test"]
    hidden = {parameter.opts[0] for parameter in command.params if parameter.hidden}
    assert hidden == {"--cli", "--sanitize"}
