# test_commands.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests that every CLI which registers the shared test command declares the same options."""

from pathlib import Path

import pytest
import typer

from sushicore import build_admission
from sushicore.console_memory import RecordingConsole
from sushicore.profile import ModuleProfile
from typer.testing import CliRunner

from sushicore.testing import commands as test_commands
from sushicore.testing import ModuleTests, register_test_command

pytestmark = pytest.mark.small


def _app(**keywords):
    profile = ModuleProfile(name="sushitrack", program="st", env_prefix="ST", root_marker="m")
    console = RecordingConsole()
    module = ModuleTests(profile=profile, project_root=lambda: Path("."), console=lambda: console,
                         build_tree=lambda: Path("."), run_ctest=lambda tree, **keywords: 0,
                         run=lambda command, cwd: 0, **keywords)
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


@pytest.fixture
def given_jobs(monkeypatch):
    """Records the job count the command hands to the run, with sixteen hardware threads."""
    monkeypatch.delenv("CMAKE_BUILD_PARALLEL_LEVEL", raising=False)
    monkeypatch.setattr(build_admission.os, "cpu_count", lambda: 16)
    seen = []
    monkeypatch.setattr(test_commands, "run_tests", lambda module, selection, **keywords: seen.append((keywords["jobs"], keywords["ceiling"])) or 0)
    return seen


def test_the_command_hands_the_threads_less_four_as_the_ceiling_when_no_flag_or_config_key_is_given(given_jobs):
    CliRunner().invoke(_app(), ["test"])
    assert given_jobs == [(None, 12)]


def test_the_command_hands_the_configured_count_as_the_ceiling_over_the_default(given_jobs):
    CliRunner().invoke(_app(configured_jobs=lambda: 6), ["test"])
    assert given_jobs == [(None, 6)]


def test_the_command_hands_the_flag_as_the_exact_count_beside_the_configured_ceiling(given_jobs):
    CliRunner().invoke(_app(configured_jobs=lambda: 6), ["test", "-j", "2"])
    assert given_jobs == [(2, 6)]


def test_the_command_hands_the_own_tests_run_only_the_flag_so_it_can_name_an_ignored_one(given_jobs):
    CliRunner().invoke(_app(cli_tests=lambda selection: 0), ["test", "--cli"])
    assert given_jobs == [(None, None)]
