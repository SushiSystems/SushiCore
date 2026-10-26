# test_package_environment.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests for the environment of a library build."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.provision.sushi_packages.package_environment import (
    K_COMPILER,
    K_MARKER,
    PackageEnvironment,
    package_variable,
)

pytestmark = pytest.mark.small


def test_the_variable_is_the_upper_case_name_with_package():
    """Check the spelling of the variable that hands a prefix down."""
    assert package_variable("sushiruntime") == "SUSHIRUNTIME_PACKAGE"


def test_the_environment_carries_compiler_marker_and_prefixes():
    """Check that the compiler, the marker and one variable per package are set."""
    env = PackageEnvironment({"PATH": "/bin"}).assemble(
        "clang++", {"sushilog": Path("/p/log"), "sushiruntime": Path("/p/rt")})
    assert env[K_COMPILER] == "clang++"
    assert env[K_MARKER] == "1"
    assert env["SUSHILOG_PACKAGE"] == str(Path("/p/log"))
    assert env["SUSHIRUNTIME_PACKAGE"] == str(Path("/p/rt"))
    assert env["PATH"] == "/bin"


def test_no_dir_variable_is_set():
    """Check that no variable ending in _DIR is added."""
    env = PackageEnvironment({}).assemble("c", {"sushilog": Path("/p")})
    assert not [key for key in env if key.endswith("_DIR")]


def test_a_package_variable_of_the_parent_is_replaced():
    """Check that a variable the parent had for a library not below is dropped."""
    parent = {"SUSHIBLAS_PACKAGE": "/old", "SUSHILOG_PACKAGE": "/old-log"}
    env = PackageEnvironment(parent).assemble("c", {"sushilog": Path("/new")})
    assert "SUSHIBLAS_PACKAGE" not in env
    assert env["SUSHILOG_PACKAGE"] == str(Path("/new"))
