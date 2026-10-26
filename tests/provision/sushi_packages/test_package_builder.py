# test_package_builder.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests for the builder that drives a library's own CLI."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.provision.sushi_packages.build_tree import BuildTree
from sushicore.provision.sushi_packages.compiler_check import CompilerCheck
from sushicore.provision.sushi_packages.package_builder import BuildRequest, CliPackageBuilder
from sushicore.provision.sushi_packages.package_environment import K_COMPILER, PackageEnvironment
from sushicore.provision.sushi_packages.package_error import PackageError

from .package_fakes import make_key

pytestmark = pytest.mark.medium


class _Runner:
    """Records commands and answers an exit code per call."""

    def __init__(self, codes=(0, 0)) -> None:
        """Answer *codes* in order."""
        self.codes = list(codes)
        self.calls: list[tuple[list[str], Path, dict]] = []

    def __call__(self, command, cwd, env) -> int:
        """Record the call and answer the next code."""
        self.calls.append((command, cwd, dict(env)))
        return self.codes.pop(0)


def _probe(command):
    """Answer a version text per compiler path."""
    return 0, f"version of {command[0]}"


def _builder(runner, warnings=None):
    """Return a builder over *runner*."""
    return CliPackageBuilder(runner, CompilerCheck(_probe, (warnings or []).append),
                             PackageEnvironment({"PATH": "p"}))


def _request(tmp_path, **changes):
    """Return a build request for a runtime in *tmp_path*."""
    key = changes.pop("key", make_key(options=("--distributed",)))
    return BuildRequest(key, tmp_path, "sr", tmp_path / "out" / "prefix", "clang++",
                        changes.get("below", {"sushilog": Path("/p/log")}))


def test_the_two_commands_run_in_order_in_the_checkout(tmp_path):
    """Check the build then package commands, their folder and the lean flag."""
    runner = _Runner()
    request = _request(tmp_path)
    _builder(runner).build(request)
    tree = BuildTree("release", ("--distributed",), "tc").folder
    build, package = (call[0] for call in runner.calls)
    assert build == ["sr", "build", "--type", "release", "--build-dir", f"build/{tree}",
                     "--lean", "--distributed"]
    assert package == ["sr", "package", "--build-dir", f"build/{tree}", "--prefix",
                       str(request.prefix), "--no-archive", "--force"]
    assert all(call[1] == tmp_path for call in runner.calls)


def test_the_environment_carries_the_compiler_and_the_packages_below(tmp_path):
    """Check that both commands run with the assembled environment."""
    runner = _Runner()
    _builder(runner).build(_request(tmp_path))
    env = runner.calls[0][2]
    assert env[K_COMPILER] == "clang++" and env["SUSHILOG_PACKAGE"] == str(Path("/p/log"))


def test_a_failed_build_does_not_run_the_package_command(tmp_path):
    """Check that the install is not attempted after a failed build."""
    runner = _Runner(codes=(2,))
    with pytest.raises(PackageError, match="exit 2"):
        _builder(runner).build(_request(tmp_path))
    assert len(runner.calls) == 1


def test_a_failed_install_raises_with_the_command(tmp_path):
    """Check that a failing package command raises naming it."""
    with pytest.raises(PackageError, match="sr package"):
        _builder(_Runner(codes=(0, 1))).build(_request(tmp_path))


def test_the_compiler_is_checked_before_the_build_and_before_the_install(tmp_path):
    """Check that an existing tree of another compiler stops the build before any command."""
    tree = tmp_path / "build" / BuildTree("release", ("--distributed",), "tc").folder
    tree.mkdir(parents=True)
    (tree / "CMakeCache.txt").write_text("CMAKE_CXX_COMPILER:FILEPATH=/other/clang++\n",
                                         encoding="utf-8")
    runner = _Runner()
    with pytest.raises(PackageError, match="another|identity"):
        _builder(runner).build(_request(tmp_path))
    assert runner.calls == []
