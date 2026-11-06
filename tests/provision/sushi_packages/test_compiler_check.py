# test_compiler_check.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the compiler check of a build tree."""

from __future__ import annotations

import pytest

from sushicore.provision.sushi_packages.compiler_check import CompilerCheck
from sushicore.provision.sushi_packages.lines_memory import RecordedLines
from sushicore.provision.sushi_packages.package_error import PackageError
from sushicore.provision.sushi_packages.toolchain_identity import MemoryProbe

pytestmark = pytest.mark.medium

#: The identity of a compiler that prints "version a": the head of the SHA-256 of that text.
K_IDENTITY_A = "ba8f572bb021017e"

#: The identity of a compiler that prints "version b".
K_IDENTITY_B = "00cdde5e73006be0"


def _probe() -> MemoryProbe:
    """Return a probe where /a/clang++ prints "version a" and /b/clang++ prints "version b"."""
    return MemoryProbe({"/a/clang++": (0, "version a"), "/b/clang++": (0, "version b")})


def _tree(tmp_path, compiler):
    """Return a build tree whose cache names *compiler*."""
    (tmp_path / "CMakeCache.txt").write_text(f"CMAKE_CXX_COMPILER:FILEPATH={compiler}\n",
                                             encoding="utf-8")
    return tmp_path


def test_a_tree_of_the_expected_compiler_passes(tmp_path):
    """Check that a tree whose cached compiler has the expected identity passes."""
    tree = _tree(tmp_path, "/a/clang++")
    assert CompilerCheck(_probe()).verify(tree, K_IDENTITY_A) is None


def test_a_tree_of_another_compiler_raises_naming_both(tmp_path):
    """Check that another compiler is refused with both identities in the message."""
    tree = _tree(tmp_path, "/a/clang++")
    with pytest.raises(PackageError) as caught:
        CompilerCheck(_probe()).verify(tree, K_IDENTITY_B)
    assert K_IDENTITY_A in str(caught.value)
    assert K_IDENTITY_B in str(caught.value)


def test_a_tree_with_no_cache_passes_with_one_warning(tmp_path):
    """Check that an unconfigured tree is not refused and warns once."""
    warnings = RecordedLines()
    CompilerCheck(_probe(), warnings).verify(tmp_path, "anything")
    assert len(warnings.lines) == 1
