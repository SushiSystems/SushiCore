# test_build_tree.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Each build type has a tree of its own, and a tree never takes another type."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.build_tree import package_build_type, refuse_another_build_type, tree_dir
from sushicore.errors import ConfigError


def _is_refused(build_dir: Path, build_type: str) -> bool:
    """Return whether configuring *build_dir* as *build_type* is refused."""
    try:
        refuse_another_build_type(build_dir, build_type)
    except ConfigError:
        return True
    return False


@pytest.mark.small
def test_a_tree_is_named_by_its_type():
    root = Path("repo")
    assert tree_dir(root, "default", "RelWithDebInfo") == root / "build" / "default-relwithdebinfo"


@pytest.mark.medium
@pytest.mark.parametrize(("requested", "refused"), [("Debug", False), ("Release", True)])
def test_a_tree_of_one_type_refuses_another(tmp_path, requested, refused):
    build_dir = tmp_path / "default-debug"
    build_dir.mkdir()
    (build_dir / "CMakeCache.txt").write_text("CMAKE_BUILD_TYPE:STRING=Debug\n")
    assert _is_refused(build_dir, requested) is refused


@pytest.mark.medium
def test_a_tree_not_yet_configured_takes_any_type(tmp_path):
    assert _is_refused(tmp_path / "default-debug", "Release") is False


@pytest.mark.small
def test_the_type_is_never_set_through_a_define():
    with pytest.raises(ConfigError):
        refuse_another_build_type(Path("tree"), "Debug", ("CMAKE_BUILD_TYPE:STRING=Release",))


@pytest.mark.small
@pytest.mark.parametrize(("build_type", "sanitized", "expected"), [
    ("Debug", False, "release"),
    ("MinSizeRel", False, "release"),
    ("Release", False, "release"),
    ("RelWithDebInfo", False, "relwithdebinfo"),
    ("RelWithDebInfo", True, "release"),
])
def test_a_debug_or_sanitized_consumer_links_release_packages(build_type, sanitized, expected):
    assert package_build_type(build_type, sanitized=sanitized) == expected
