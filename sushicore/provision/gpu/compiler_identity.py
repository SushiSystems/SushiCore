# compiler_identity.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026 Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Reading which intel/llvm commit a SYCL compiler was built from."""

from __future__ import annotations

import re
import subprocess
import typing
from pathlib import Path

#: Matches the clang version line that names the intel/llvm commit the compiler was built from.
_COMMIT_PATTERN = re.compile(
    r"clang version [^\s]+ \(https://github\.com/intel/llvm(?:\.git)? ([0-9a-f]{40})\)"
)


def read_intel_llvm_commit(
    clang_path: Path,
    run: typing.Callable[..., subprocess.CompletedProcess] = subprocess.run,
) -> str | None:
    """Return the intel/llvm commit *clang_path* was built from, or None.

    :param clang_path: Path to the compiler binary to query with ``--version``.
    :param run: Injected in place of :func:`subprocess.run` for tests.
    :return: The 40-character commit hash, or None on failure, timeout, or a
        version string that names no intel/llvm commit.
    """
    try:
        result = run(
            [str(clang_path), "--version"],
            capture_output=True, text=True, timeout=15,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    match = _COMMIT_PATTERN.search(result.stdout or "")
    return match.group(1) if match else None
