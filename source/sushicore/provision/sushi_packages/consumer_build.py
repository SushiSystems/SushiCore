# consumer_build.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""What a consumer CLI takes from a resolved package set: configure arguments and run-time folders."""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Protocol

from ...build_env import prepend_path
from .package_set import PackageSet

#: The search path variable a Windows program finds its DLLs on.
K_WINDOWS_PATH = "PATH"

#: The search path variable a Linux program finds its shared objects on.
K_POSIX_PATH = "LD_LIBRARY_PATH"


class _Definitions(Protocol):
    """A module config that names the checkouts of the pinned libraries it does not package."""

    def sushi_definitions(self, root: Path, packaged: PackageSet | None = None) -> list[str]:
        """Return the ``-D<NAME>_DIR`` arguments of the pins *packaged* does not cover."""


def configure_arguments(config: _Definitions, root: Path, packages: PackageSet) -> list[str]:
    """Return the ``-D`` arguments a configure takes for *packages*.

    They are the config folder of every package and the checkout directory of each pinned
    library that is not a package.

    Args:
        config: The consumer's module config.
        root: The consumer's project root.
        packages: The packages the resolver chose.
    """
    return [*config.sushi_definitions(root, packages), *packages.definitions()]


def search_path_variable(windows: bool) -> str:
    """Return the variable a program of this platform finds its libraries on."""
    return K_WINDOWS_PATH if windows else K_POSIX_PATH


class RunDirs:
    """Keeps the run-time folders of the packages a build tree linked, in a file of that tree.

    The build writes the folders; the commands that run the tree read them, so none of them
    resolves the packages again.
    """

    def __init__(self, file_name: str) -> None:
        """Name the file the folders are kept in, such as ``.sushiruntime_package_dirs.json``."""
        self._file_name = file_name

    def save(self, tree: Path, dirs: Sequence[str]) -> None:
        """Write *dirs* into *tree*, making the folder when it is not there."""
        tree.mkdir(parents=True, exist_ok=True)
        (tree / self._file_name).write_text(json.dumps(list(dirs)), encoding="utf-8")

    def read(self, tree: Path) -> list[str]:
        """Return the folders written into *tree*, none when there is no valid file."""
        try:
            found = json.loads((Path(tree) / self._file_name).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return []
        if not isinstance(found, list):
            return []
        return [item for item in found if isinstance(item, str)]

    def prepend(self, env: dict[str, str], dirs: Sequence[str], windows: bool) -> None:
        """Put *dirs* first on the library search path of *env*."""
        prepend_path(env, search_path_variable(windows), list(dirs))
