# cmake_driver_port.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The port a CLI drives cmake and ctest through, with the build-tree reads it needs."""

from __future__ import annotations

from pathlib import Path
from typing import Mapping, Protocol, Sequence


class CMakeDriverPort(Protocol):
    """What a CLI asks of a CMake driver: the commands, and what a build tree holds.

    :class:`sushicore.cmake_driver.CMakeDriver` runs real commands over real trees;
    :class:`sushicore.cmake_driver_memory.MemoryCMakeDriver` keeps its trees in memory.
    """

    def cmake(self, cfg) -> str:
        """Returns the cmake executable: the configured path if set, else 'cmake'."""

    def ctest(self, cfg) -> str:
        """Returns the ctest executable: the configured path if set, else 'ctest'."""

    def tree_exists(self, build_dir: Path) -> bool:
        """Returns whether a build tree is at *build_dir*."""

    def cached_value(self, build_dir: Path, entry: str) -> str | None:
        """Returns the value the tree's cache holds for *entry*, or None."""

    def needs_configure(self, build_dir: Path, generator: str, *,
                        expect: Mapping[str, str] | None = None,
                        root: Path | None = None) -> bool:
        """Returns whether *build_dir* must be configured before it can be built."""

    def configure(self, args: Sequence[str], cwd: Path, env=None) -> int:
        """Runs a configure whose argv the caller assembled and returns its exit code."""

    def compile(self, cfg, build_dir: Path, cwd: Path, env, *,
                config: str | None = None, targets: Sequence[str] = (),
                jobs: int | None = None) -> int:
        """Brings a configured tree up to date and returns the build's exit code."""

    def ctest_run(self, cfg, build_dir: Path, env, *,
                  label_regex: str | None = None, exclude_label_regex: str | None = None,
                  filter: str | None = None,
                  repeat: int = 0, jobs: int | None = None,
                  config: str | None = None, output_junit: Path | None = None,
                  shuffle_seed: int | None = None, gtest_filter: str | None = None) -> int:
        """Runs the tests of *build_dir* and returns ctest's exit code."""

    def clean_tree(self, build_dir: Path) -> bool:
        """Removes *build_dir* and returns whether it is gone."""

    def doxygen(self, cfg, doxyfile: Path, cwd: Path, env, *, install_hint: str = ...) -> int:
        """Runs Doxygen over *doxyfile* and returns its exit code, or 1 when it cannot run."""
