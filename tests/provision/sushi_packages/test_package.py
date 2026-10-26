# test_package.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests for what a consumer reads from an installed package."""

from __future__ import annotations

import pytest

from sushicore.provision.sushi_packages.package import Package
from sushicore.provision.sushi_packages.package_error import PackageError
from sushicore.provision.sushi_packages.package_store import PackageStore

from .package_fakes import install, make_key

pytestmark = pytest.mark.medium


@pytest.fixture
def store(tmp_path):
    """Return a store under a temporary folder."""
    return PackageStore(tmp_path / "packages")


def test_the_config_folder_keeps_the_spelling_of_the_library(store):
    """Check that the folder named after the library is found with its own case."""
    package = install(store, make_key("sushiblas"))
    assert package.config_folder().name == "SushiBLAS"


def test_an_install_without_a_config_raises(store):
    """Check that a prefix with no config file for the library is refused."""
    key = make_key("sushiblas")
    store.stage(key).mkdir()
    package = store.commit(key, 0.0)
    with pytest.raises(PackageError, match="holds no CMake config"):
        package.config_folder()


def test_run_dirs_are_bin_on_windows(store):
    """Check that Windows names bin and not lib."""
    package = install(store, make_key())
    assert [path.name for path in package.run_dirs("windows")] == ["bin"]


def test_run_dirs_are_the_existing_lib_folders_elsewhere(store):
    """Check that Linux names lib and lib64 where they exist."""
    package = install(store, make_key())
    (package.prefix / "lib64").mkdir()
    assert [path.name for path in package.run_dirs("linux")] == ["lib", "lib64"]


def test_below_lists_the_packages_the_stamp_records(store):
    """Check that the stamp's below entries come back as pairs."""
    key = make_key("sushiblas", below=(("sushiruntime", "abc"),))
    assert install(store, key).below() == [("sushiruntime", "abc")]


def test_the_toolchain_and_build_type_come_from_the_stamp(store):
    """Check that the package reports the parts its stamp recorded."""
    package: Package = install(store, make_key(toolchain="tc9", build_type="debug"))
    assert (package.toolchain, package.build_type) == ("tc9", "debug")
