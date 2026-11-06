# test_package_environment.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
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


@pytest.mark.parametrize("name, variable", [
    ("sushiruntime", "SUSHIRUNTIME_PACKAGE"),
    ("sushilog", "SUSHILOG_PACKAGE"),
])
def test_the_variable_is_the_upper_case_name_with_package(name, variable):
    """Check the spelling of the variable that hands a prefix down."""
    assert package_variable(name) == variable


def test_the_environment_carries_the_compiler():
    """Check that the compiler variable holds the compiler given."""
    assert PackageEnvironment({}).assemble("clang++", {})[K_COMPILER] == "clang++"


def test_the_environment_carries_the_nested_marker():
    """Check that the nested marker is set."""
    assert PackageEnvironment({}).assemble("clang++", {})[K_MARKER] == "1"


def test_the_environment_holds_one_variable_per_package_below():
    """Check that each package below is named by its own variable holding its prefix."""
    env = PackageEnvironment({}).assemble(
        "clang++", {"sushilog": Path("/p/log"), "sushiruntime": Path("/p/rt")})
    assert (env["SUSHILOG_PACKAGE"], env["SUSHIRUNTIME_PACKAGE"]) == (
        str(Path("/p/log")), str(Path("/p/rt")))


def test_the_environment_keeps_the_variables_of_the_parent():
    """Check that a variable of the parent unrelated to packages is kept."""
    assert PackageEnvironment({"PATH": "/bin"}).assemble("clang++", {})["PATH"] == "/bin"


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
