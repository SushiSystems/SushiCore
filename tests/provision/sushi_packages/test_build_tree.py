# test_build_tree.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests for the name of a package build tree."""

from __future__ import annotations

import pytest

from sushicore.provision.sushi_packages.build_tree import BuildTree

pytestmark = pytest.mark.small


def test_the_name_is_stable_for_equal_input():
    """Check that equal configurations share one folder."""
    first, second = (BuildTree("release", ("--a",), "tc") for _ in range(2))
    assert first.folder == second.folder


@pytest.mark.parametrize("other", [
    BuildTree("debug", ("--a",), "tc"),
    BuildTree("release", (), "tc"),
    BuildTree("release", ("--a",), "tc2"),
])
def test_each_part_gives_another_folder(other):
    """Check that a changed build type, option set or toolchain gives another folder."""
    assert other.folder != BuildTree("release", ("--a",), "tc").folder


def test_the_folder_is_pkg_and_twelve_hex_digits():
    """Check the shape of the folder name."""
    folder = BuildTree("release", (), "tc").folder
    assert folder.startswith("pkg-") and len(folder) == len("pkg-") + 12
