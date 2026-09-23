# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""The intel/llvm commit is parsed from a clang --version line, or reported absent."""

from __future__ import annotations

import subprocess
from pathlib import Path

from sushicore.provision.gpu.compiler_identity import read_intel_llvm_commit

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
    def run(*args, **kwargs):
        return type("Result", (), {"stdout": stdout})()
    return run


def test_reads_the_commit_from_the_dpcpp_version_line():
    commit = read_intel_llvm_commit(Path("clang++"), run=_run_returning(_DPCPP_VERSION))
    assert commit == "d169ba4e202112988439e56372560bacfdb9824b"


def test_reads_the_commit_from_the_development_build_version_line():
    commit = read_intel_llvm_commit(Path("clang++"), run=_run_returning(_DEV_BUILD_VERSION))
    assert commit == "d5f649b706f63b5c74e1929bc95db8de91085560"


def test_reads_the_commit_when_the_remote_url_carries_a_dot_git_suffix():
    commit = read_intel_llvm_commit(Path("clang++"), run=_run_returning(_DOT_GIT_VERSION))
    assert commit == "d169ba4e202112988439e56372560bacfdb9824b"


def test_a_non_intel_clang_reports_no_commit():
    commit = read_intel_llvm_commit(Path("clang++"), run=_run_returning(_NON_INTEL_VERSION))
    assert commit is None


def test_a_raising_run_reports_no_commit():
    def run(*args, **kwargs):
        raise OSError("compiler not found")
    assert read_intel_llvm_commit(Path("clang++"), run=run) is None


def test_a_timing_out_run_reports_no_commit():
    def run(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="clang++", timeout=15)
    assert read_intel_llvm_commit(Path("clang++"), run=run) is None
