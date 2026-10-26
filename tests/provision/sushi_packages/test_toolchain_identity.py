# test_toolchain_identity.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests for the identity of a SYCL compiler."""

from __future__ import annotations

import json

import pytest

from sushicore.provision.sushi_packages.package_error import PackageError
from sushicore.provision.sushi_packages.toolchain_identity import compiler_identity

pytestmark = pytest.mark.medium


def _probe(text, code=0):
    """Return a probe that answers *text* with exit code *code*."""
    return lambda _command: (code, text)


def test_the_same_version_text_gives_one_identity(tmp_path):
    """Check that two compilers printing the same text have one identity."""
    compiler = str(tmp_path / "bin" / "clang++")
    assert compiler_identity(compiler, _probe("clang 1")) == compiler_identity(
        compiler, _probe("clang 1"))


def test_another_version_text_gives_another_identity(tmp_path):
    """Check that a compiler printing other text has another identity."""
    compiler = str(tmp_path / "bin" / "clang++")
    assert compiler_identity(compiler, _probe("clang 1")) != compiler_identity(
        compiler, _probe("clang 2"))


def test_the_stamp_tag_is_joined(tmp_path):
    """Check that the tag of the install's toolchain stamp ends the identity."""
    (tmp_path / "bin").mkdir()
    (tmp_path / ".sushi_toolchain.json").write_text(json.dumps({"tag": "nightly-1"}),
                                                    encoding="utf-8")
    identity = compiler_identity(str(tmp_path / "bin" / "clang++"), _probe("clang 1"))
    assert identity.endswith(":nightly-1")


@pytest.mark.parametrize("text, code", [("", 0), ("clang 1", 1)])
def test_a_compiler_that_gives_no_identity_raises(tmp_path, text, code):
    """Check that empty output or a failing exit code is refused."""
    with pytest.raises(PackageError, match="no identity"):
        compiler_identity(str(tmp_path / "clang++"), _probe(text, code))
