# compiler_identity.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Reading which intel/llvm commit a SYCL compiler was built from."""

from __future__ import annotations

import re
from pathlib import Path

from ...proc import CommandRunner, did_not_run
from ..process_run import provision_runner

#: Matches the clang version line that names the intel/llvm commit the compiler was built from.
_COMMIT_PATTERN = re.compile(
    r"clang version [^\s]+ \(https://github\.com/intel/llvm(?:\.git)? ([0-9a-f]{40})\)"
)


def read_intel_llvm_commit(clang_path: Path, runner: CommandRunner | None = None) -> str | None:
    """Return the intel/llvm commit *clang_path* was built from, or None.

    :param clang_path: Path to the compiler binary to query with ``--version``.
    :param runner: Runs the compiler; the provision runner when ``None``.
    :return: The 40-character commit hash, or None on failure, timeout, or a
        version string that names no intel/llvm commit.
    """
    code, out, err = (runner or provision_runner()).capture(
        [str(clang_path), "--version"], timeout=15)
    if did_not_run(str(clang_path), code, err):
        return None
    match = _COMMIT_PATTERN.search(out or "")
    return match.group(1) if match else None
