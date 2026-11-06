# test_cmake_cache.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Reading CMakeCache.txt, which is cheaper and more robust than `cmake -L`."""

import os
from pathlib import Path

import pytest

from sushicore.cmake_cache import (cached_value, generator_sentinel,
                                   home_directory, is_stale)


_CACHE = """\
# This is the CMakeCache file.
CMAKE_BUILD_TYPE:STRING=RelWithDebInfo
CMAKE_HOME_DIRECTORY:INTERNAL=/workspace/sushiengine
SUSHIENGINE_EXECUTION_BACKEND:STRING=runtime
"""


def _tree(tmp_path: Path) -> Path:
    (tmp_path / "CMakeCache.txt").write_text(_CACHE, encoding="utf-8")
    return tmp_path


def _tree_of(tmp_path: Path, configured: bool) -> Path:
    """Return *tmp_path* as a configured tree, or as it is when *configured* is False."""
    return _tree(tmp_path) if configured else tmp_path


@pytest.mark.medium
def test_cached_value_reads_an_entry(tmp_path):
    assert cached_value(_tree(tmp_path), "CMAKE_BUILD_TYPE") == "RelWithDebInfo"


@pytest.mark.medium
def test_cached_value_is_none_for_an_absent_entry(tmp_path):
    assert cached_value(_tree(tmp_path), "NOT_PRESENT") is None


@pytest.mark.medium
def test_cached_value_is_none_for_an_unconfigured_tree(tmp_path):
    assert cached_value(tmp_path, "CMAKE_BUILD_TYPE") is None


@pytest.mark.medium
def test_a_prefix_does_not_match_a_longer_entry(tmp_path):
    """CMAKE_BUILD must not match CMAKE_BUILD_TYPE."""
    assert cached_value(_tree(tmp_path), "CMAKE_BUILD") is None


@pytest.mark.medium
def test_home_directory_is_the_configured_source_path(tmp_path):
    assert home_directory(_tree(tmp_path)) == "/workspace/sushiengine"


@pytest.mark.medium
@pytest.mark.parametrize(("configured", "root", "stale"), [
    (True, "/d/Projects/sushiengine", True),
    (True, "/workspace/sushiengine", False),
    (False, "/anywhere", False),
])
def test_a_tree_is_stale_only_when_configured_for_another_path(tmp_path, configured, root, stale):
    assert is_stale(_tree_of(tmp_path, configured), Path(root)) is stale


@pytest.mark.medium
@pytest.mark.skipif(os.name != "nt", reason="only Windows ignores case and separators")
def test_is_stale_ignores_case_and_separators_as_windows_does(tmp_path):
    (tmp_path / "CMakeCache.txt").write_text(
        "CMAKE_HOME_DIRECTORY:INTERNAL=D:/Projects/SushiEngine\n", encoding="utf-8")
    assert is_stale(tmp_path, Path(r"d:\projects\sushiengine")) is False


@pytest.mark.small
@pytest.mark.parametrize(("generator", "sentinel"), [("Ninja", "build.ninja"), ("Unix Makefiles", "Makefile")])
def test_the_sentinel_follows_the_generator(generator, sentinel):
    assert generator_sentinel(generator) == sentinel
