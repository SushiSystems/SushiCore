# test_package_command.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests for the shared package command a library CLI registers."""

from __future__ import annotations

import pytest
import typer
from typer.testing import CliRunner

from sushicore.profile import ModuleProfile
from sushicore.provision.commands import ModuleProvision
from sushicore.provision.config import ProvisionSettings
from sushicore.provision.package_command import register_package_command

pytestmark = pytest.mark.medium


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
        console=lambda: console), run=runner)
    return app


def _built(root, tree="build/default-debug"):
    """Create a configured build tree *tree* under *root*."""
    (root / tree).mkdir(parents=True)
    (root / tree / "CMakeCache.txt").write_text(
        f"CMAKE_HOME_DIRECTORY:INTERNAL={root}\n", encoding="utf-8")


def test_the_command_installs_the_default_tree_to_the_default_prefix(tmp_path, recording_console):
    """Check that package with no argument installs the default Debug tree into build/dist."""
    root = tmp_path / "lib"
    _built(root)
    calls = []

    def runner(command, cwd, env=None):
        """Record the command and succeed."""
        calls.append(command)
        return 0

    result = CliRunner().invoke(_app(root, runner, recording_console), ["package", "--no-archive"])
    assert result.exit_code == 0
    assert calls[0][:3] == ["/c/cmake", "--install", str(root / "build" / "default-debug")]
    assert calls[0][4] == str((root / "build" / "dist").resolve())


def test_the_command_installs_the_tree_it_is_told_to(tmp_path, recording_console):
    """Check that --build-dir overrides the default tree."""
    root = tmp_path / "lib"
    _built(root, "build/pkg-x")
    calls = []

    def runner(command, cwd, env=None):
        """Record the command and succeed."""
        calls.append(command)
        return 0

    result = CliRunner().invoke(_app(root, runner, recording_console),
                                ["package", "--no-archive", "--build-dir", "build/pkg-x"])
    assert result.exit_code == 0
    assert calls[0][:3] == ["/c/cmake", "--install", str(root / "build" / "pkg-x")]


def test_the_command_exits_non_zero_for_a_tree_that_is_not_built(tmp_path, recording_console):
    """Check the exit code of a package run with no build."""
    root = tmp_path / "lib"
    root.mkdir()
    result = CliRunner().invoke(_app(root, lambda *_a, **_k: 0, recording_console), ["package"])
    assert result.exit_code == 1
