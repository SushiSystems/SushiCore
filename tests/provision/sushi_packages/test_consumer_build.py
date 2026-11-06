# test_consumer_build.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for what a consumer takes from a resolved package set."""

from __future__ import annotations

import os

import pytest

from sushicore.provision.sushi_packages.consumer_build import (
    MemoryDefinitions,
    RunDirs,
    configure_arguments,
    search_path_variable,
)
from sushicore.provision.sushi_packages.package_set import PackageSet, ResolvedPackage
from sushicore.provision.sushi_packages.package_store import PackageStore

from .package_fakes import install, make_key

K_FILE = ".consumer_package_dirs.json"


@pytest.mark.medium
def test_the_configure_arguments_join_the_pins_and_the_package_folders(tmp_path):
    """Check that the pins no package covers come first, then the folder of each package."""
    package = install(PackageStore(tmp_path / "packages"), make_key("sushilog"))
    packages = PackageSet((ResolvedPackage(package, None, built=False),))
    config = MemoryDefinitions(["sushilog", "other"])
    expected = [f"-DOTHER_DIR={tmp_path / 'other'}",
                f"-DSushiLog_DIR={package.root / 'prefix' / 'lib' / 'cmake' / 'SushiLog'}"]
    assert configure_arguments(config, tmp_path, packages) == expected


@pytest.mark.small
def test_the_search_path_variable_follows_the_platform():
    """Check both platforms."""
    assert search_path_variable(True) == "PATH"
    assert search_path_variable(False) == "LD_LIBRARY_PATH"


@pytest.mark.medium
def test_saved_folders_are_read_back_and_the_tree_is_made(tmp_path):
    """Check a round trip into a tree that did not exist."""
    tree = tmp_path / "a" / "build"
    RunDirs(K_FILE).save(tree, ["/one", "/two"])
    assert RunDirs(K_FILE).read(tree) == ["/one", "/two"]


@pytest.mark.medium
@pytest.mark.parametrize("text, folders", [
    ("not json", []),
    ('{"a": 1}', []),
    ('["/one", 2]', ["/one"]),
])
def test_a_file_that_is_not_a_list_of_texts_reads_as_far_as_it_can(tmp_path, text, folders):
    """Check that a bad file never raises and gives the texts it holds."""
    (tmp_path / K_FILE).write_text(text, encoding="utf-8")
    assert RunDirs(K_FILE).read(tmp_path) == folders


@pytest.mark.medium
def test_a_tree_without_the_file_has_no_folders(tmp_path):
    """Check the missing file."""
    assert RunDirs(K_FILE).read(tmp_path) == []


@pytest.mark.small
def test_the_folders_lead_the_path_of_the_platform():
    """Check both variables and that the old value stays after the folders."""
    posix = {"LD_LIBRARY_PATH": "/old"}
    RunDirs(K_FILE).prepend(posix, ["/one"], windows=False)
    assert posix["LD_LIBRARY_PATH"].split(os.pathsep) == ["/one", "/old"]
    windows = {"PATH": "/old"}
    RunDirs(K_FILE).prepend(windows, ["/one"], windows=True)
    assert windows["PATH"].split(os.pathsep) == ["/one", "/old"]
