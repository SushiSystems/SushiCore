# test_shard_registrations.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests reading the shard registrations of a build tree."""

from pathlib import Path

import pytest

from sushicore.files_memory import MemoryFiles
from sushicore.testing.shard_registrations import shard_registrations

pytestmark = pytest.mark.small

K_TREE = Path("/repo/build")
K_FILE = (
    'add_test([=[core.small_shard_1of2]=] "/repo/build/core.exe" "--gtest_filter=Small_*:*/Small_*-Small_Slow.*"'
    ' "--gtest_output=xml:/repo/build/test_results/gtest/core.small_shard_1of2.xml")\n'
    'set_tests_properties([=[core.small_shard_1of2]=] PROPERTIES  ENVIRONMENT "GTEST_TOTAL_SHARDS=2;GTEST_SHARD_INDEX=1"'
    ' LABELS "small;quarantined" TIMEOUT "1260" _BACKTRACE_TRIPLES "a.cmake;1;add_test")\n'
    'add_test([=[Small_A.One]=] "/repo/build/core.exe")\n')


def test_a_shard_registration_carries_its_filter_environment_labels_and_timeout():
    found = shard_registrations(K_TREE, MemoryFiles({K_TREE / "CTestTestfile.cmake": K_FILE}))
    assert len(found) == 1
    shard = found[0]
    assert (shard.name, shard.program, shard.size_filter) == (
        "core.small_shard_1of2", "core", "Small_*:*/Small_*-Small_Slow.*")
    assert shard.environment == {"GTEST_TOTAL_SHARDS": "2", "GTEST_SHARD_INDEX": "1"}
    assert (shard.labels, shard.timeout, shard.arguments) == (("small", "quarantined"), 1260.0, ())


def test_a_test_with_no_shard_variables_is_no_shard():
    text = 'add_test([=[core.small]=] "/repo/build/core.exe" "--gtest_filter=Small_*")\n'
    assert shard_registrations(K_TREE, MemoryFiles({K_TREE / "CTestTestfile.cmake": text})) == []
