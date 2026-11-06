# test_diag_commands.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests the diagnostic commands a CLI registers."""

from dataclasses import dataclass
from pathlib import Path

import pytest

import typer

from typer.testing import CliRunner

from sushicore.console_memory import RecordingConsole
from sushicore.diag import Diagnostics
from sushicore.diag_commands import register_diagnostic_commands
from sushicore.diag_memory import InMemoryConfigModule
from sushicore.files_memory import MemoryFiles
from sushicore.profile import ModuleProfile

pytestmark = pytest.mark.small



@dataclass
class _Settings:
    cxx: str = ""


def _app(*, build_env=None, env: bool = True) -> tuple[typer.Typer, RecordingConsole]:
    """Returns an application named `sx` with one command and the diagnostics registered.

    The diagnostics read an in-memory config module and no file; *build_env* is what they dump.
    """
    app = typer.Typer(name="sx", help="Builds things.", no_args_is_help=True, add_completion=False)

    @app.command("build")
    def build() -> None:
        """Configure and build."""

    console = RecordingConsole()
    diagnostics = Diagnostics(
        profile=ModuleProfile(name="SushiTest", program="sx", env_prefix="SX"), console=console,
        config=InMemoryConfigModule(Path("module"), _Settings), build_env=build_env,
        files=MemoryFiles())
    register_diagnostic_commands(app, diagnostics, program="sx", panel="Diagnostics", env=env)
    return app, console



def test_the_config_command_prints_the_resolved_configuration_and_exits_zero():
    """config calls the config diagnostic and exits with the code it returns."""
    app, console = _app()
    result = CliRunner().invoke(app, ["config"])
    assert result.exit_code == 0
    assert console.texts("header") == ["Resolved Configuration"]



def test_the_env_command_exits_with_the_code_of_the_env_diagnostic():
    """env exits 1, as the diagnostic returns, when the CLI has no build environment."""
    app, console = _app()
    result = CliRunner().invoke(app, ["env"])
    assert result.exit_code == 1
    assert console.texts("error") == ["sx has no build environment to dump."]



@pytest.mark.parametrize("flag", ["--all", "-a"])
def test_the_env_command_shows_every_variable_with_the_all_flag(flag):
    """--all and -a reach the diagnostic as show_all."""
    app, console = _app(build_env=lambda cfg, build_dir: {"PATH": "/bin", "UNRELATED_THING": "x"})
    result = CliRunner().invoke(app, ["env", flag])
    assert result.exit_code == 0
    assert console.texts("info") == ["2 of 2 variables shown"]



def test_diagnostic_commands_can_leave_env_to_the_cli():
    """A CLI whose env takes its own flags registers config alone."""
    app, _ = _app(env=False)
    assert CliRunner().invoke(app, ["env"]).exit_code == 2
