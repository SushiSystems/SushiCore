# test_build_tree.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Each build type has a tree of its own, and a tree never takes another type."""

from __future__ import annotations

import pytest

from sushicore.build_tree import K_DEFAULT_BUILD_TYPE, refuse_another_build_type, tree_dir
from sushicore.errors import ConfigError

pytestmark = pytest.mark.small


def test_a_tree_is_named_by_its_type(tmp_path):
    assert tree_dir(tmp_path, "default", "RelWithDebInfo") == tmp_path / "build" / "default-relwithdebinfo"
    assert K_DEFAULT_BUILD_TYPE == "Debug"


def test_a_tree_of_one_type_refuses_another(tmp_path):
    build_dir = tmp_path / "default-debug"
    refuse_another_build_type(build_dir, "Debug")
    build_dir.mkdir()
    (build_dir / "CMakeCache.txt").write_text("CMAKE_BUILD_TYPE:STRING=Debug\n")
    refuse_another_build_type(build_dir, "Debug")
    with pytest.raises(ConfigError):
        refuse_another_build_type(build_dir, "Release")


def test_the_type_is_never_set_through_a_define(tmp_path):
    with pytest.raises(ConfigError):
        refuse_another_build_type(tmp_path, "Debug", ("CMAKE_BUILD_TYPE:STRING=Release",))
