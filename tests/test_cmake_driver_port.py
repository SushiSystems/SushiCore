# test_cmake_driver_port.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The contract of the CMake driver port, kept by the disk driver and the in-memory driver alike."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from sushicore.cmake_driver import CMakeDriver
from sushicore.cmake_driver_memory import MemoryCMakeDriver
from sushicore.console_memory import RecordingConsole
from sushicore.proc_memory import RecordingRunner

pytestmark = pytest.mark.medium

K_CACHE = {"CMAKE_BUILD_TYPE": "Debug", "CMAKE_HOME_DIRECTORY": "src"}


class _DiskSide:
    """A CMakeDriver over trees written under a temp folder."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.driver = CMakeDriver(RecordingConsole(), RecordingRunner(RecordingConsole()))

    def add_tree(self, build_dir: Path, cache: dict[str, str]) -> None:
        build_dir.mkdir(parents=True)
        (build_dir / "build.ninja").write_text("", encoding="utf-8")
        lines = [f"{name}:STRING={value}" for name, value in cache.items()]
        (build_dir / "CMakeCache.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


class _MemorySide:
    """A MemoryCMakeDriver over trees held in memory."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.driver = MemoryCMakeDriver(RecordingConsole())

    def add_tree(self, build_dir: Path, cache: dict[str, str]) -> None:
        self.driver.add_tree(build_dir, generator="Ninja", cache=cache)


@pytest.fixture(params=["disk", "memory"])
def side(request, tmp_path):
    """Each driver in turn, rooted at a temp folder."""
    return (_DiskSide if request.param == "disk" else _MemorySide)(tmp_path)


def _cache(side) -> dict[str, str]:
    """The cache of a tree configured from the side's own source folder."""
    return {**K_CACHE, "CMAKE_HOME_DIRECTORY": str(side.root / "src")}


def test_an_absent_tree_needs_a_configure_and_holds_no_value(side):
    build_dir = side.root / "build"
    assert not side.driver.tree_exists(build_dir)
    assert side.driver.cached_value(build_dir, "CMAKE_BUILD_TYPE") is None
    assert side.driver.needs_configure(build_dir, "Ninja")


def test_a_configured_tree_answers_its_cache_and_needs_no_configure(side):
    build_dir = side.root / "build"
    side.add_tree(build_dir, _cache(side))
    assert side.driver.tree_exists(build_dir)
    assert side.driver.cached_value(build_dir, "CMAKE_BUILD_TYPE") == "Debug"
    assert not side.driver.needs_configure(build_dir, "Ninja", expect={"CMAKE_BUILD_TYPE": "Debug"},
                                           root=side.root / "src")


def test_a_tree_off_its_expected_value_needs_a_configure(side):
    build_dir = side.root / "build"
    side.add_tree(build_dir, _cache(side))
    assert side.driver.needs_configure(build_dir, "Ninja", expect={"CMAKE_BUILD_TYPE": "Release"})


def test_a_tree_of_another_source_folder_needs_a_configure(side):
    build_dir = side.root / "build"
    side.add_tree(build_dir, _cache(side))
    assert side.driver.needs_configure(build_dir, "Ninja", root=side.root / "elsewhere")


def test_a_cleaned_tree_is_gone(side):
    build_dir = side.root / "build"
    side.add_tree(build_dir, _cache(side))
    assert side.driver.clean_tree(build_dir)
    assert not side.driver.tree_exists(build_dir)


def test_a_missing_doxyfile_returns_one(side):
    cfg = SimpleNamespace(doxygen_exe="", expand=lambda text: text)
    assert side.driver.doxygen(cfg, side.root / "Doxyfile", side.root, None) == 1


def test_a_build_and_a_test_run_return_zero_when_nothing_fails(side):
    build_dir = side.root / "build"
    side.add_tree(build_dir, _cache(side))
    cfg = SimpleNamespace(cmake_exe="", ctest_exe="", expand=lambda text: text)
    assert side.driver.compile(cfg, build_dir, side.root, {}) == 0
    assert side.driver.ctest_run(cfg, build_dir, {}) == 0
