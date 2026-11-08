# test_package_command.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the shared package command a library CLI registers."""

from __future__ import annotations

import pytest
import typer
from typer.testing import CliRunner

from sushicore.console_memory import RecordingConsole
from sushicore.profile import ModuleProfile
from sushicore.provision.commands import ModuleProvision
from sushicore.provision.config import ProvisionSettings
from sushicore.provision.package_command import register_package_command
from sushicore.provision.package_install import CapturedRun


def _app(root, runner, console):
    """Return an app carrying the package command over *root*."""
    profile = ModuleProfile(name="sushilog", program="sl", env_prefix="SL",
                            root_marker="sushilog.marker")
    app = typer.Typer()

    @app.callback()
    def _root():
        """Test app."""

    register_package_command(app, ModuleProvision(
        profile=profile, project_root=lambda: root,
        load_config=lambda: ProvisionSettings(platform="linux", cmake_exe="/c/cmake"),
        console=lambda: console), run=runner,
        capture=lambda command, cwd, env=None: CapturedRun(runner(command, cwd, env), ""))
    return app


def _built(root, tree="build/default-debug"):
    """Create a configured build tree *tree* under *root*."""
    (root / tree).mkdir(parents=True)
    (root / tree / "CMakeCache.txt").write_text(
        f"CMAKE_HOME_DIRECTORY:INTERNAL={root}\n", encoding="utf-8")


def _install_command(root, *arguments):
    """Run ``package --no-archive`` with *arguments* over *root*; return the exit code and the first command."""
    calls = []

    def runner(command, cwd, env=None):
        """Record the command and succeed."""
        calls.append(command)
        return 0

    result = CliRunner().invoke(_app(root, runner, RecordingConsole()),
                                ["package", "--no-archive", *arguments])
    return result.exit_code, calls[0] if calls else []


@pytest.mark.medium
def test_the_command_installs_the_default_tree(tmp_path):
    """Check that package with no argument installs the default Debug tree."""
    root = tmp_path / "lib"
    _built(root)
    code, command = _install_command(root)
    assert code == 0
    assert command[:3] == ["/c/cmake", "--install", str(root / "build" / "default-debug")]


@pytest.mark.medium
def test_the_command_installs_to_the_default_prefix(tmp_path):
    """Check that package with no argument installs into build/dist."""
    root = tmp_path / "lib"
    _built(root)
    _, command = _install_command(root)
    assert str((root / "build" / "dist").resolve()) in command


@pytest.mark.medium
def test_the_command_installs_the_tree_it_is_told_to(tmp_path):
    """Check that --build-dir overrides the default tree."""
    root = tmp_path / "lib"
    _built(root, "build/pkg-x")
    code, command = _install_command(root, "--build-dir", "build/pkg-x")
    assert code == 0
    assert command[:3] == ["/c/cmake", "--install", str(root / "build" / "pkg-x")]


@pytest.mark.medium
def test_the_command_exits_non_zero_for_a_tree_that_is_not_built(tmp_path):
    """Check the exit code of a package run with no build."""
    root = tmp_path / "lib"
    root.mkdir()
    result = CliRunner().invoke(_app(root, lambda *_a, **_k: 0, RecordingConsole()), ["package"])
    assert result.exit_code == 1
