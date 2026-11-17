# test_compiler_identity.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The intel/llvm commit is parsed from a clang --version line, or reported absent."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.console_memory import RecordingConsole
from sushicore.proc_memory import RecordingRunner
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


def _runner() -> RecordingRunner:
    """Return a runner that records commands and starts no process."""
    return RecordingRunner(RecordingConsole())


def _printing(version: str) -> RecordingRunner:
    """Return a runner whose ``clang++ --version`` prints *version*."""
    return _runner().script(0, tuple(version.splitlines()))


@pytest.mark.parametrize(("version", "expected"), [
    (_DPCPP_VERSION, "d169ba4e202112988439e56372560bacfdb9824b"),
    (_DEV_BUILD_VERSION, "d5f649b706f63b5c74e1929bc95db8de91085560"),
    (_DOT_GIT_VERSION, "d169ba4e202112988439e56372560bacfdb9824b"),
], ids=["dpcpp", "development-build", "dot-git-suffix"])
def test_reads_the_commit_from_an_intel_llvm_version_line(version, expected):
    """Check that the commit after the intel/llvm URL is read from each version line shape."""
    assert read_intel_llvm_commit(Path("clang++"), _printing(version)) == expected


def test_a_non_intel_clang_reports_no_commit():
    """Check that a version line naming no intel/llvm commit gives None."""
    assert read_intel_llvm_commit(Path("clang++"), _printing(_NON_INTEL_VERSION)) is None


@pytest.mark.parametrize("runner", [
    _runner().script_missing(),
    _runner().script_timeout(),
], ids=["missing", "timing-out"])
def test_a_failing_run_reports_no_commit(runner):
    """Check that a compiler that cannot start or times out gives None."""
    assert read_intel_llvm_commit(Path("clang++"), runner) is None
