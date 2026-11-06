# test_package_builder.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the builder that drives a library's own CLI."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.provision.sushi_packages.build_tree import BuildTree
from sushicore.provision.sushi_packages.compiler_check import CompilerCheck
from sushicore.provision.sushi_packages.lines_memory import RecordedLines
from sushicore.provision.sushi_packages.package_builder import (
    BuildRequest,
    CliPackageBuilder,
    MemoryRun,
)
from sushicore.provision.sushi_packages.package_environment import K_COMPILER, PackageEnvironment
from sushicore.provision.sushi_packages.package_error import PackageError
from sushicore.provision.sushi_packages.toolchain_identity import MemoryProbe

from .package_fakes import make_key

pytestmark = pytest.mark.medium

K_OTHER = "/other/clang++"
K_TREE = BuildTree("release", ("--distributed",), "tc").folder


def _builder(run):
    """Return a builder over *run*, whose probe finds another compiler than the key's."""
    check = CompilerCheck(MemoryProbe({K_OTHER: (0, "version b")}), RecordedLines())
    return CliPackageBuilder(run, check, PackageEnvironment({"PATH": "p"}))


def _request(tmp_path):
    """Return a build request for a runtime in *tmp_path*."""
    key = make_key(options=("--distributed",))
    return BuildRequest(key, tmp_path, "sr", tmp_path / "out" / "prefix", "clang++",
                        {"sushilog": Path("/p/log")})


def _write_cache(tmp_path):
    """Write, into the build tree of the request, a cache that names another compiler."""
    tree = tmp_path / "build" / K_TREE
    tree.mkdir(parents=True)
    (tree / "CMakeCache.txt").write_text(f"CMAKE_CXX_COMPILER:FILEPATH={K_OTHER}\n",
                                         encoding="utf-8")


def test_the_build_command_runs_before_the_package_command(tmp_path):
    """Check the order of the two commands."""
    run = MemoryRun()
    _builder(run).build(_request(tmp_path))
    assert [call[0][1] for call in run.calls] == ["build", "package"]


def test_the_build_command_names_the_type_the_tree_and_the_lean_options(tmp_path):
    """Check the arguments of the build command."""
    run = MemoryRun()
    _builder(run).build(_request(tmp_path))
    assert run.calls[0][0] == ["sr", "build", "--type", "release", "--build-dir",
                               f"build/{K_TREE}", "--lean", "--distributed"]


def test_the_package_command_names_the_tree_and_the_prefix(tmp_path):
    """Check the arguments of the package command."""
    run = MemoryRun()
    request = _request(tmp_path)
    _builder(run).build(request)
    assert run.calls[1][0] == ["sr", "package", "--build-dir", f"build/{K_TREE}", "--prefix",
                               str(request.prefix), "--no-archive", "--force"]


def test_both_commands_run_in_the_checkout(tmp_path):
    """Check the folder both commands run in."""
    run = MemoryRun()
    _builder(run).build(_request(tmp_path))
    assert [call[1] for call in run.calls] == [tmp_path, tmp_path]


def test_both_commands_run_with_the_compiler_and_the_packages_below(tmp_path):
    """Check that the assembled environment reaches both commands."""
    run = MemoryRun()
    _builder(run).build(_request(tmp_path))
    assert [(call[2][K_COMPILER], call[2]["SUSHILOG_PACKAGE"]) for call in run.calls] == [
        ("clang++", str(Path("/p/log")))] * 2


def test_a_failed_build_does_not_run_the_package_command(tmp_path):
    """Check that the install is not attempted after a failed build."""
    run = MemoryRun(codes=(2,))
    with pytest.raises(PackageError, match="exit 2"):
        _builder(run).build(_request(tmp_path))
    assert len(run.calls) == 1


def test_a_failed_install_raises_with_the_command(tmp_path):
    """Check that a failing package command raises naming it."""
    with pytest.raises(PackageError, match="sr package"):
        _builder(MemoryRun(codes=(0, 1))).build(_request(tmp_path))


def test_the_compiler_is_checked_before_the_build(tmp_path):
    """Check that an existing tree of another compiler stops the build before any command."""
    _write_cache(tmp_path)
    run = MemoryRun()
    with pytest.raises(PackageError, match="identity"):
        _builder(run).build(_request(tmp_path))
    assert run.calls == []


def test_the_compiler_is_checked_before_the_install(tmp_path):
    """Check that a build leaving a tree of another compiler stops before the package command."""
    run = MemoryRun(effects=[lambda: _write_cache(tmp_path)])
    with pytest.raises(PackageError, match="identity"):
        _builder(run).build(_request(tmp_path))
    assert [call[0][1] for call in run.calls] == ["build"]
