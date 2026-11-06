# test_toolchain_identity.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the identity of a SYCL compiler."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.provision.sushi_packages.package_error import PackageError
from sushicore.provision.sushi_packages.toolchain_identity import MemoryProbe, compiler_identity

pytestmark = pytest.mark.small

K_COMPILER = str(Path("toolchain") / "bin" / "clang++")


def _no_stamp(_install):
    """Read the stamp of an install that has none."""
    return {}


def _identity(text, stamp=_no_stamp):
    """Return the identity of the compiler when it prints *text*."""
    return compiler_identity(K_COMPILER, MemoryProbe({K_COMPILER: (0, text)}), stamp)


@pytest.mark.parametrize("first, second, same", [
    ("clang 1", "clang 1", True),
    ("clang 1", "clang 2", False),
])
def test_the_identity_follows_the_version_text(first, second, same):
    """Check that equal version text gives one identity and other text gives another."""
    assert (_identity(first) == _identity(second)) is same


def test_the_stamp_tag_is_joined():
    """Check that the tag of the install's toolchain stamp ends the identity."""
    assert _identity("clang 1", lambda _install: {"tag": "nightly-1"}) == (
        "0e11ac7dd454af18:nightly-1")


@pytest.mark.parametrize("text, code", [("", 0), ("clang 1", 1)])
def test_a_compiler_that_gives_no_identity_raises(text, code):
    """Check that empty output or a failing exit code is refused."""
    with pytest.raises(PackageError, match="no identity"):
        compiler_identity(K_COMPILER, MemoryProbe({K_COMPILER: (code, text)}), _no_stamp)
