"""Reading CMakeCache.txt, which is cheaper and more robust than `cmake -L`."""

from pathlib import Path

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


def test_cached_value_reads_an_entry(tmp_path):
    assert cached_value(_tree(tmp_path), "CMAKE_BUILD_TYPE") == "RelWithDebInfo"


def test_cached_value_is_none_for_an_absent_entry(tmp_path):
    assert cached_value(_tree(tmp_path), "NOT_PRESENT") is None


def test_cached_value_is_none_for_an_unconfigured_tree(tmp_path):
    assert cached_value(tmp_path, "CMAKE_BUILD_TYPE") is None


def test_a_prefix_does_not_match_a_longer_entry(tmp_path):
    """CMAKE_BUILD must not match CMAKE_BUILD_TYPE."""
    assert cached_value(_tree(tmp_path), "CMAKE_BUILD") is None


def test_home_directory_is_the_configured_source_path(tmp_path):
    assert home_directory(_tree(tmp_path)) == "/workspace/sushiengine"


def test_a_tree_from_another_path_is_stale(tmp_path):
    assert is_stale(_tree(tmp_path), Path("/d/Projects/sushiengine")) is True


def test_a_tree_from_this_path_is_not_stale(tmp_path):
    assert is_stale(_tree(tmp_path), Path("/workspace/sushiengine")) is False


def test_an_unconfigured_tree_is_not_stale(tmp_path):
    assert is_stale(tmp_path, Path("/anywhere")) is False


def test_the_sentinel_follows_the_generator():
    assert generator_sentinel("Ninja") == "build.ninja"
    assert generator_sentinel("Unix Makefiles") == "Makefile"
