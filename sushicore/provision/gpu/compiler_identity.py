# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Reading which intel/llvm commit a SYCL compiler was built from.

The adapter builder needs this commit to fetch a matching Unified Runtime
checkout, so a mismatch never links against the wrong SYCL runtime.
"""

from __future__ import annotations

import re
import subprocess
import typing
from pathlib import Path

#: Matches a clang version line naming the intel/llvm commit it was built from,
#: e.g. "clang version 21.0.0git (https://github.com/intel/llvm d5f649b7...)".
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
