# test_compiler_check.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests for the compiler check of a build tree."""

from __future__ import annotations

import pytest

from sushicore.provision.sushi_packages.compiler_check import CompilerCheck
from sushicore.provision.sushi_packages.package_error import PackageError
from sushicore.provision.sushi_packages.toolchain_identity import compiler_identity

pytestmark = pytest.mark.medium


def _probe(command):
    """Answer a version text that depends on the compiler path."""
    return 0, f"version of {command[0]}"


def _tree(tmp_path, compiler):
    """Return a build tree whose cache names *compiler*."""
    (tmp_path / "CMakeCache.txt").write_text(f"CMAKE_CXX_COMPILER:FILEPATH={compiler}\n",
                                             encoding="utf-8")
    return tmp_path


def test_a_tree_of_the_expected_compiler_passes(tmp_path):
    """Check that a tree whose cached compiler has the expected identity passes."""
    tree = _tree(tmp_path, "/a/clang++")
    CompilerCheck(_probe).verify(tree, compiler_identity("/a/clang++", _probe))


def test_a_tree_of_another_compiler_raises_naming_both(tmp_path):
    """Check that another compiler is refused with both identities in the message."""
    tree = _tree(tmp_path, "/a/clang++")
    expected = compiler_identity("/b/clang++", _probe)
    with pytest.raises(PackageError) as caught:
        CompilerCheck(_probe).verify(tree, expected)
    assert expected in str(caught.value)
    assert compiler_identity("/a/clang++", _probe) in str(caught.value)


def test_a_tree_with_no_cache_passes_with_one_warning(tmp_path):
    """Check that an unconfigured tree is not refused and warns once."""
    warnings: list[str] = []
    CompilerCheck(_probe, warnings.append).verify(tmp_path, "anything")
    assert len(warnings) == 1
