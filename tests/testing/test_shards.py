# test_shards.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests naming the shards of a build and finding out whether a build registers any."""

from pathlib import Path

import pytest

from sushicore.files_memory import MemoryFiles
from sushicore.testing.shards import program_executable, program_of, registers_shards

pytestmark = pytest.mark.small

K_TREE = Path("/repo/build")
K_SHARD_FILE = 'add_test([=[core.small_shard_0of3]=] "/repo/build/core" "--gtest_filter=Small_*")\n'
K_CASE_FILE = 'add_test([=[Small_A.One]=] "/repo/build/core")\n'
K_ROOT_FILE = 'subdirs("tests")\n'


@pytest.mark.parametrize("name, program", [
    ("core_tests.small_shard_0of3", "core_tests"),
    ("a.b.medium_shard_12of40", "a.b"),
    ("core_tests.small_quarantined", None),
    ("Small_A.Case", None),
])
def test_program_of_names_the_program_of_a_shard_and_nothing_for_another_test(name, program):
    assert program_of(name) == program


def test_a_build_registers_shards_when_a_test_file_below_its_subdirs_names_one():
    files = MemoryFiles({K_TREE / "CTestTestfile.cmake": K_ROOT_FILE,
                         K_TREE / "tests" / "CTestTestfile.cmake": K_SHARD_FILE})
    assert registers_shards(K_TREE, files) is True


def test_a_build_of_one_test_per_case_registers_no_shards():
    files = MemoryFiles({K_TREE / "CTestTestfile.cmake": K_ROOT_FILE,
                         K_TREE / "tests" / "CTestTestfile.cmake": K_CASE_FILE})
    assert registers_shards(K_TREE, files) is False


def test_a_build_whose_subdirs_name_their_own_folder_ends_the_walk():
    files = MemoryFiles({K_TREE / "CTestTestfile.cmake": 'subdirs(".")\n'})
    assert registers_shards(K_TREE, files) is False


def test_a_tree_with_no_test_file_registers_no_shards():
    assert registers_shards(K_TREE, MemoryFiles()) is False


def test_the_executable_of_a_program_is_the_one_its_shards_run():
    files = MemoryFiles({K_TREE / "CTestTestfile.cmake": K_ROOT_FILE,
                         K_TREE / "tests" / "CTestTestfile.cmake": K_CASE_FILE + K_SHARD_FILE})
    assert program_executable(K_TREE, "core", files) == Path("/repo/build/core")


def test_a_program_no_shard_names_has_no_executable():
    files = MemoryFiles({K_TREE / "CTestTestfile.cmake": K_SHARD_FILE})
    assert program_executable(K_TREE, "other", files) is None
