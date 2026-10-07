# cmake_cache.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""What a build tree says about how it was configured.

Read out of CMakeCache.txt rather than through `cmake -L`, so it costs nothing
and works on a tree whose configure failed part way through -- which is exactly
when a caller most needs to know what is in there.
"""

from __future__ import annotations

import os
from pathlib import Path

#: The file a configured tree leaves behind, per generator family.
_SENTINELS = {"Ninja": "build.ninja"}


def generator_sentinel(generator: str) -> str:
    """The build file *generator* writes, whose absence means "not configured"."""
    return _SENTINELS.get(generator, "Makefile")


def cached_value(build_dir: Path, entry: str) -> str | None:
    """The value CMake baked into *build_dir*'s cache for *entry*, or None.

    @param build_dir The build tree to inspect.
    @param entry     The cache entry's name, without its ":TYPE" suffix.
    @return The value, or None when the tree is unconfigured or lacks the entry.
    """
    cache = build_dir / "CMakeCache.txt"
    if not cache.is_file():
        return None
    prefix = entry + ":"
    try:
        text = cache.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None
    for line in text.splitlines():
        if line.startswith(prefix):
            return line.split("=", 1)[1].strip()
    return None


def same_path(left: str, right: str) -> bool:
    """Report whether two spellings name one path, ignoring case and separators as the platform does."""
    return os.path.normcase(os.path.normpath(left)) == os.path.normcase(os.path.normpath(right))


def compiler_changed(build_dir: Path, compiler: str) -> bool:
    """Report whether *build_dir* was configured with a C++ compiler at another path than *compiler*.

    @return False when the tree is unconfigured or its cache names no compiler.
    """
    cached = cached_value(build_dir, "CMAKE_CXX_COMPILER")
    return bool(cached) and not same_path(cached, compiler)


def home_directory(build_dir: Path) -> str | None:
    """The source directory *build_dir* was configured against, or None."""
    return cached_value(build_dir, "CMAKE_HOME_DIRECTORY")


def is_stale(build_dir: Path, root: Path) -> bool:
    """True when the tree was configured for a different source directory.

    A build tree carried over from another machine or path -- a container volume
    build at /workspace, reused on the Windows host -- has absolute paths baked
    into its cache that no longer exist. CTest's `if(EXISTS ...)` guards then
    fail and it reports "No tests were found" while the sources are fine. The
    comparison is case- and separator-insensitive because Windows is.
    """
    home = home_directory(build_dir)
    if not home:
        return False
    return os.path.normcase(os.path.normpath(home)) != \
        os.path.normcase(os.path.normpath(str(root)))
