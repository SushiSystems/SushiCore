# test_compiler_identity.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The intel/llvm commit is parsed from a clang --version line, or reported absent."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from sushicore.provision.gpu.compiler_identity import read_intel_llvm_commit


pytestmark = pytest.mark.small

_DPCPP_VERSION = (
    "DPC++ ...\n"
    "clang version 23.0.0git "
    "(https://github.com/intel/llvm d169ba4e202112988439e56372560bacfdb9824b)\n"
)

_DOT_GIT_VERSION = (
    "clang version 23.0.0git "
    "(https://github.com/intel/llvm.git d169ba4e202112988439e56372560bacfdb9824b)\n"
)

_DEV_BUILD_VERSION = (
    "Intel SYCL compiler development build based on:\n"
    "clang version 21.0.0git "
    "(https://github.com/intel/llvm d5f649b706f63b5c74e1929bc95db8de91085560)\n"
)

_NON_INTEL_VERSION = (
    "clang version 17.0.6\n"
    "Target: x86_64-pc-windows-msvc\n"
)


def _run_returning(stdout: str):
    """Return a run function that answers *stdout* as the output of ``clang++ --version``."""
    def run(*args, **kwargs):
        """Answer a result that holds *stdout*."""
        return type("Result", (), {"stdout": stdout})()
    return run


def _run_raising(error: Exception):
    """Return a run function that raises *error*, as a compiler that cannot run does."""
    def run(*args, **kwargs):
        """Raise *error*."""
        raise error
    return run


@pytest.mark.parametrize(("version", "expected"), [
    (_DPCPP_VERSION, "d169ba4e202112988439e56372560bacfdb9824b"),
    (_DEV_BUILD_VERSION, "d5f649b706f63b5c74e1929bc95db8de91085560"),
    (_DOT_GIT_VERSION, "d169ba4e202112988439e56372560bacfdb9824b"),
], ids=["dpcpp", "development-build", "dot-git-suffix"])
def test_reads_the_commit_from_an_intel_llvm_version_line(version, expected):
    """Check that the commit after the intel/llvm URL is read from each version line shape."""
    assert read_intel_llvm_commit(Path("clang++"), run=_run_returning(version)) == expected


def test_a_non_intel_clang_reports_no_commit():
    """Check that a version line naming no intel/llvm commit gives None."""
    assert read_intel_llvm_commit(Path("clang++"), run=_run_returning(_NON_INTEL_VERSION)) is None


@pytest.mark.parametrize("error", [
    OSError("compiler not found"),
    subprocess.TimeoutExpired(cmd="clang++", timeout=15),
], ids=["raising", "timing-out"])
def test_a_failing_run_reports_no_commit(error):
    """Check that a run that raises or times out gives None."""
    assert read_intel_llvm_commit(Path("clang++"), run=_run_raising(error)) is None
