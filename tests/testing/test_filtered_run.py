# test_filtered_run.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests running the shards of a tree under a filter of the caller."""

from pathlib import Path

import pytest

from sushicore.console_memory import RecordingConsole
from sushicore.files_memory import MemoryFiles
from sushicore.profile import ModuleProfile
from sushicore.testing.filtered_run import run_filtered_shards
from sushicore.testing.labels import TestLabel, select_labels
from sushicore.testing.module_tests import ModuleTests
from sushicore.testing.result_files import failed_tests

pytestmark = pytest.mark.small

K_TREE = Path("/repo/build")
K_JUNIT = K_TREE / "Testing" / "junit.xml"


def _shard(name, size, index, count, labels, timeout, filter_text=None):
    filter_text = filter_text or f"{size.title()}_*"
    return (f'add_test([=[core.{name}]=] "/repo/build/core" "--gtest_filter={filter_text}")\n'
            f'set_tests_properties([=[core.{name}]=] PROPERTIES ENVIRONMENT '
            f'"GTEST_TOTAL_SHARDS={count};GTEST_SHARD_INDEX={index}" LABELS "{labels}" TIMEOUT "{timeout}")\n')


K_FILE = (_shard("small_shard_0of2", "small", 0, 2, "small", 60) + _shard("small_shard_1of2", "small", 1, 2, "small", 60)
          + _shard("medium_shard_0of1", "medium", 0, 1, "medium", 300)
          + _shard("small_quarantined", "small", 0, 1, "small;quarantined", 30, "Small_Flaky.*"))


class _Programs:
    def __init__(self, failing=()):
        self.calls = []
        self.failing = failing

    def __call__(self, program, arguments, *, env=None, timeout=None):
        self.calls.append((program, arguments, env, timeout))
        return 1 if any(name in arguments[0] for name in self.failing) else 0


def _run(programs, user_filter, jobs=2, repeat=0, seed=None):
    files = MemoryFiles({K_TREE / "CTestTestfile.cmake": K_FILE})
    profile = ModuleProfile(name="core", program="co", env_prefix="CO", root_marker="m")
    module = ModuleTests(profile=profile, project_root=lambda: Path("/repo"), console=RecordingConsole,
                         build_tree=lambda: K_TREE, run_ctest=None, run=None, run_program=programs)
    code = run_filtered_shards(module, K_TREE, select_labels(None), user_filter, jobs=jobs,
                               repeat=repeat, shuffle_seed=seed, junit=K_JUNIT, files=files)
    return code, files


def test_each_selected_shard_runs_with_its_size_kept_in_the_users_filter_and_its_variables_and_timeout():
    programs = _Programs()
    assert _run(programs, "Small_Rect.*")[0] == 0
    assert sorted((call[2]["GTEST_SHARD_INDEX"], call[3]) for call in programs.calls) == [("0", 60.0), ("1", 60.0)]
    assert all(call[1][0] == "--gtest_filter=Small_Rect.*" and call[0] == "core" for call in programs.calls)
    assert all(call[1][-1].startswith("--gtest_output=xml:") and "small_shard" in call[1][-1]
               for call in programs.calls)


def test_a_shard_of_another_size_than_the_filter_names_is_not_run_and_quarantined_ones_are_left_out():
    programs = _Programs()
    _run(programs, "Medium_*")
    assert [call[2]["GTEST_TOTAL_SHARDS"] for call in programs.calls] == ["1"]
    assert programs.calls[0][3] == 300.0


def test_a_filter_that_matches_no_shard_runs_nothing_and_passes():
    programs = _Programs()
    assert _run(programs, "Large_*")[0] == 0 and programs.calls == []


def test_a_failed_shard_fails_the_run_and_is_named_failed_in_the_junit_file():
    code, files = _run(_Programs(failing=("Small_",)), "Small_*")
    assert code == 1 and sorted(failed_tests(files.read_text(K_JUNIT))) == [
        "core.small_shard_0of2", "core.small_shard_1of2"]


def test_the_shuffle_seed_and_the_repeat_reach_the_program():
    programs = _Programs()
    _run(programs, "Small_*", jobs=1, repeat=3, seed=7)
    assert programs.calls[0][2]["GTEST_RANDOM_SEED"] == "7" and "--gtest_repeat=3" in programs.calls[0][1]


def test_shards_that_need_an_accelerator_run_in_turn_in_their_registered_order():
    text = "".join(_shard(f"large_shard_{index}of4", "large", index, 4, "large", 120) for index in range(4))
    text = text.replace('TIMEOUT "120"', 'TIMEOUT "120" RESOURCE_GROUPS "gpus:1"')
    files = MemoryFiles({K_TREE / "CTestTestfile.cmake": text})
    order = []

    def program(name, arguments, *, env=None, timeout=None):
        order.append(env["GTEST_SHARD_INDEX"])
        return 0

    profile = ModuleProfile(name="core", program="co", env_prefix="CO", root_marker="m")
    module = ModuleTests(profile=profile, project_root=lambda: Path("/repo"), console=RecordingConsole,
                         build_tree=lambda: K_TREE, run_ctest=None, run=None, run_program=program)
    code = run_filtered_shards(module, K_TREE, select_labels([TestLabel.LARGE]), "Large_*", jobs=4,
                               repeat=0, shuffle_seed=None, junit=K_JUNIT, files=files)
    assert (code, order) == (0, ["0", "1", "2", "3"])

