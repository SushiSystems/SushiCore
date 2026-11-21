# tree_reuse.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Refuses a build tree CMake cannot configure again, so a build never removes one.

The reasoning is in docs/architecture/OVERVIEW.md, section `tree_reuse`.
"""

from __future__ import annotations

from pathlib import Path

from .cmake_cache import same_path
from .cmake_driver_port import CMakeDriverPort
from .errors import ConfigError

#: The generators a tree configured with the platform default can hold.
_K_DEFAULT_GENERATOR_FAMILIES = ("Visual Studio", "Unix Makefiles", "Xcode")


def refuse_unreusable_tree(driver: CMakeDriverPort, build_dir: Path, *, generator: str,
                           root: Path, program: str) -> None:
    """Raises ConfigError when CMake cannot configure *build_dir* again for this build.

    CMake cannot change a tree's generator, and cannot move a tree to another source folder, in
    place. The build says so and leaves the tree to `<program> clean`; every other difference is
    configured in place.

    Args:
        generator: The generator this build wants; empty is the platform default.
        root: The checkout this build configures.
        program: The CLI's name, which the message points at.
    """
    if not driver.tree_exists(build_dir):
        return
    configured = driver.configured_generator(build_dir)
    if configured is not None and _is_another_generator(configured, generator):
        raise ConfigError(
            f"{build_dir} was configured with {configured}, and this build uses "
            f"{generator or 'the platform default'}. CMake cannot change that in place. "
            f"Remove the tree with `{program} clean` (it lists the trees and removes them with "
            f"--yes), then build again.")
    home = driver.cached_value(build_dir, "CMAKE_HOME_DIRECTORY")
    if home and not same_path(home, str(root)):
        raise ConfigError(
            f"{build_dir} was configured for {home}, and this checkout is {root}. CMake cannot "
            f"move a tree to another source folder. Remove the tree with `{program} clean` (it "
            f"lists the trees and removes them with --yes), then build again.")


def _is_another_generator(configured: str, wanted: str) -> bool:
    """Tells whether *configured* is a generator other than *wanted*; empty is the default."""
    if wanted == "":
        return not configured.startswith(_K_DEFAULT_GENERATOR_FAMILIES)
    return configured != wanted
