# glob_search.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Finds a tool by glob pattern or by a list of candidate paths, and names the well-known patterns."""

from __future__ import annotations

import glob
from pathlib import Path

K_ICX_GLOBS = [
    r"C:/Program Files (x86)/Intel/oneAPI/compiler/*/bin/icx-cl.exe",
    r"C:/Program Files/Intel/oneAPI/compiler/*/bin/icx-cl.exe",
]
K_RC_GLOBS = [
    r"C:/Program Files (x86)/Windows Kits/10/bin/*/x64/rc.exe",
    r"C:/Program Files/Windows Kits/10/bin/*/x64/rc.exe",
]
# Neither the apt CUDA toolkit nor oneAPI add themselves to PATH, so these well-known install locations are checked directly.
K_NVCC_GLOBS_LINUX = [
    "/usr/local/cuda/bin/nvcc",
    "/usr/local/cuda-*/bin/nvcc",
]
K_ICX_GLOBS_LINUX = [
    "/opt/intel/oneapi/compiler/*/bin/icpx",
    "/opt/intel/oneapi/compiler/*/bin/icx",
]


def first_glob_match(patterns: list[str]) -> str:
    """Return the last (highest-sorting) match among *patterns*, or ''."""
    for pat in patterns:
        hits = sorted(glob.glob(pat))
        if hits:
            return hits[-1]  # latest version when sorted
    return ""


def first_existing(paths: list[str]) -> str:
    """Return the first path in *paths* that exists, or ''."""
    for p in paths:
        if Path(p).exists():
            return p
    return ""
