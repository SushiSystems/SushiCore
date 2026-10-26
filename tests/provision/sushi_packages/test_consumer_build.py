# test_consumer_build.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests for what a consumer takes from a resolved package set."""

from __future__ import annotations

import os

import pytest

from sushicore.provision.sushi_packages.consumer_build import (
    RunDirs,
    configure_arguments,
    search_path_variable,
)
from sushicore.provision.sushi_packages.package_set import PackageSet

pytestmark = pytest.mark.small

K_FILE = ".consumer_package_dirs.json"


class _Config:
    """Names one pinned library that is not a package, and records what it was asked."""

    def __init__(self) -> None:
        """Start with no request recorded."""
        self.asked: list[tuple] = []

    def sushi_definitions(self, root, packaged=None):
        """Record the request and return the unpackaged pin."""
        self.asked.append((root, packaged))
        return ["-DOTHER_DIR=/checkout/other"]


def test_the_configure_arguments_join_the_pins_and_the_package_folders(tmp_path):
    """Check the order and that the package set reaches the config."""
    config, packages = _Config(), PackageSet(())
    assert configure_arguments(config, tmp_path, packages) == ["-DOTHER_DIR=/checkout/other"]
    assert config.asked == [(tmp_path, packages)]


def test_the_search_path_variable_follows_the_platform():
    """Check both platforms."""
    assert search_path_variable(True) == "PATH"
    assert search_path_variable(False) == "LD_LIBRARY_PATH"


def test_saved_folders_are_read_back_and_the_tree_is_made(tmp_path):
    """Check a round trip into a tree that did not exist."""
    tree = tmp_path / "a" / "build"
    RunDirs(K_FILE).save(tree, ["/one", "/two"])
    assert RunDirs(K_FILE).read(tree) == ["/one", "/two"]


@pytest.mark.parametrize("text", ["not json", '{"a": 1}', '["/one", 2]'])
def test_a_file_that_is_not_a_list_of_texts_reads_as_far_as_it_can(tmp_path, text):
    """Check that a bad file never raises."""
    (tmp_path / K_FILE).write_text(text, encoding="utf-8")
    assert RunDirs(K_FILE).read(tmp_path) == (["/one"] if text.endswith("2]") else [])


def test_a_tree_without_the_file_has_no_folders(tmp_path):
    """Check the missing file."""
    assert RunDirs(K_FILE).read(tmp_path) == []


def test_the_folders_lead_the_path_of_the_platform():
    """Check both variables and that the old value stays after the folders."""
    posix = {"LD_LIBRARY_PATH": "/old"}
    RunDirs(K_FILE).prepend(posix, ["/one"], windows=False)
    assert posix["LD_LIBRARY_PATH"].split(os.pathsep) == ["/one", "/old"]
    windows = {"PATH": "C:/old"}
    RunDirs(K_FILE).prepend(windows, ["C:/one"], windows=True)
    assert windows["PATH"].split(os.pathsep) == ["C:/one", "C:/old"]
