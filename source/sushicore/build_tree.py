# build_tree.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Names a build tree by its build type, and keeps each tree to the type in its name.

The reasoning is in docs/architecture/OVERVIEW.md, section `build_tree`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from .cmake_cache import cached_value
from .errors import ConfigError

#: The build type every Sushi CLI builds unless told otherwise.
K_DEFAULT_BUILD_TYPE = "Debug"


def tree_dir(root: Path, name: str, build_type: str) -> Path:
    """Returns `build/<name>-<type>` under *root*, the one tree of *name* for *build_type*."""
    return Path(root) / "build" / f"{name}-{build_type.lower()}"


def refuse_another_build_type(build_dir: Path, build_type: str,
                              defines: Sequence[str] = ()) -> None:
    """Raises ConfigError when a configure would give *build_dir* a build type not its own.

    A tree configured as another type would recompile every unit under that type's flags and
    stop being the tree its name says. *defines* are the caller's extra `VAR=VALUE` entries; one
    naming CMAKE_BUILD_TYPE is refused, because the type picks the tree.
    """
    for define in defines:
        if define.split("=", 1)[0].split(":", 1)[0] == "CMAKE_BUILD_TYPE":
            raise ConfigError(f"-D {define}: the build type is chosen with --type, which picks "
                              f"the tree of that type")
    cached = cached_value(build_dir, "CMAKE_BUILD_TYPE") if Path(build_dir).is_dir() else None
    if cached and cached != build_type:
        raise ConfigError(f"{build_dir} is a {cached} tree; a {build_type} build has a tree of "
                          f"its own. Delete {build_dir} if its name is wrong.")
