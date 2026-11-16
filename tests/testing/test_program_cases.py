# test_program_cases.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the listing that tells which test program holds a suite."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.files_memory import MemoryFiles
from sushicore.testing.program_cases import (
    executable_modified_time,
    listing_is_current,
    may_hold_a_case,
    suites_by_program,
)

pytestmark = pytest.mark.small

K_TREE = Path("/repo/build")
K_REGISTRY = (
    'add_test([=[core.small_shard_0of1]=] "/repo/build/core" "--gtest_filter=Small_*")\n'
    'add_test([=[json.small_shard_0of1]=] "/repo/build/json" "--gtest_filter=Small_*")\n'
)


def _files(listing, **built):
    """Return files holding the registry, the listing at time 10 and each program at its time."""
    files = MemoryFiles(
        {K_TREE / "CTestTestfile.cmake": K_REGISTRY, K_TREE / "Testing" / "programs.json": listing},
        {K_TREE / "Testing" / "programs.json": 10, **{K_TREE / name: at for name, at in built.items()}},
    )
    return files


def test_a_program_with_unknown_suites_may_hold_any_case():
    assert may_hold_a_case(None, "Small_Json.*") and may_hold_a_case(frozenset(), "Small_Json.*")


@pytest.mark.parametrize("user_filter, expected", [
    ("Small_Json.*", True),
    ("Small_Rect.*", False),
    ("*", True),
])
def test_a_program_may_hold_a_case_only_when_the_filter_can_reach_one_of_its_suites(user_filter, expected):
    assert may_hold_a_case(frozenset({"Small_Json"}), user_filter) is expected


@pytest.mark.parametrize("listing_time, program_time, expected", [
    (10.0, 5.0, True),
    (10.0, 10.0, True),
    (10.0, 20.0, False),
    (None, 5.0, False),
    (10.0, None, False),
])
def test_a_listing_is_current_only_when_it_is_not_older_than_the_program(listing_time, program_time, expected):
    assert listing_is_current(listing_time, program_time) is expected


def test_the_modified_time_falls_back_to_the_path_with_exe_and_is_none_when_neither_is_known():
    path = Path("/repo/build/core")
    assert executable_modified_time(MemoryFiles({}, {path.with_name("core.exe"): 7.0}), path) == 7.0
    assert executable_modified_time(MemoryFiles({}, {path: 3.0}), path) == 3.0
    assert executable_modified_time(MemoryFiles({}), path) is None


def test_suites_are_grouped_by_the_program_that_holds_them():
    files = _files('{"Small_Json": "json", "Grid": "json", "Small_Rect": "core"}', core=5, json=5)
    assert suites_by_program(K_TREE, files) == {
        "json": frozenset({"Small_Json", "Grid"}),
        "core": frozenset({"Small_Rect"}),
    }


@pytest.mark.parametrize("listing", [None, "not json", "[1, 2]"])
def test_a_missing_or_unreadable_listing_gives_no_entry(listing):
    files = _files(listing, core=5, json=5)
    if listing is None:
        files.remove(K_TREE / "Testing" / "programs.json")
    assert suites_by_program(K_TREE, files) == {}


def test_a_program_built_after_the_listing_or_with_no_known_time_gets_no_entry():
    files = _files('{"Small_Json": "json", "Small_Rect": "core"}', core=20)
    assert suites_by_program(K_TREE, files) == {}
