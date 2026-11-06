# test_forced_packages.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the packages a parent hands to a nested build."""

from __future__ import annotations

import pytest

from sushicore.provision.sushi_packages.forced_packages import ForcedPackages
from sushicore.provision.sushi_packages.lines_memory import RecordedLines
from sushicore.provision.sushi_packages.package_error import PackageError
from sushicore.provision.sushi_packages.package_store import PackageStore

from .package_fakes import install, make_key

pytestmark = pytest.mark.medium


@pytest.fixture
def store(tmp_path):
    """Return a store holding one runtime package."""
    return PackageStore(tmp_path / "packages")


def test_without_the_marker_a_variable_is_ignored_with_one_warning(store):
    """Check that a stale shell variable chooses nothing and warns once."""
    package = install(store, make_key())
    warnings = RecordedLines()
    env = {"SUSHIRUNTIME_PACKAGE": str(package.prefix)}
    forced = ForcedPackages(env, store, warnings).read(["sushiruntime"], "tc", "release")
    assert (forced, len(warnings.lines)) == ({}, 1)


def test_with_the_marker_the_package_is_taken(store):
    """Check that a nested build takes the package its parent named."""
    package = install(store, make_key())
    env = {"SUSHISTACK_PACKAGE_NESTED": "1", "SUSHIRUNTIME_PACKAGE": str(package.prefix)}
    forced = ForcedPackages(env, store).read(["sushiruntime"], "tc", "release")
    assert forced["sushiruntime"].digest == package.digest


def test_a_lower_case_variable_name_is_read_as_its_package_variable(store):
    """Check that the marker and the variable are found whatever the case of their names."""
    package = install(store, make_key())
    env = {"sushistack_package_nested": "1", "sushiruntime_package": str(package.prefix)}
    forced = ForcedPackages(env, store).read(["sushiruntime"], "tc", "release")
    assert forced["sushiruntime"].digest == package.digest


def test_a_library_without_a_variable_is_not_forced(store):
    """Check that only the libraries with a variable come back."""
    env = {"SUSHISTACK_PACKAGE_NESTED": "1"}
    assert ForcedPackages(env, store).read(["sushilog"], "tc", "release") == {}


@pytest.mark.parametrize("toolchain, build_type", [("other", "release"), ("tc", "debug")])
def test_another_toolchain_or_build_type_is_refused(store, toolchain, build_type):
    """Check that a package of another toolchain or build type is refused."""
    package = install(store, make_key())
    env = {"SUSHISTACK_PACKAGE_NESTED": "1", "SUSHIRUNTIME_PACKAGE": str(package.prefix)}
    with pytest.raises(PackageError, match="toolchain tc and build type release"):
        ForcedPackages(env, store).read(["sushiruntime"], toolchain, build_type)


def test_a_digest_that_is_not_in_the_store_is_refused(store, tmp_path):
    """Check that a prefix outside the store is refused."""
    env = {"SUSHISTACK_PACKAGE_NESTED": "1",
           "SUSHIRUNTIME_PACKAGE": str(tmp_path / "x" / "deadbeef" / "prefix")}
    with pytest.raises(PackageError, match="not a complete package"):
        ForcedPackages(env, store).read(["sushiruntime"], "tc", "release")
