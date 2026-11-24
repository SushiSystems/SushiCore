# test_shard_case_run.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests running some cases of one shard as the shard runs them under CTest."""

from pathlib import Path

import pytest

from sushicore.console_memory import RecordingConsole
from sushicore.files_memory import MemoryFiles
from sushicore.profile import ModuleProfile
from sushicore.testing.module_tests import ModuleTests
from sushicore.testing.shard_case_run import run_shard_cases

pytestmark = pytest.mark.small

K_TREE = Path("/repo/build")
K_REPORT = K_TREE / "test_results" / "slow" / "core.small_shard_1of2.xml"
K_FILE = ('add_test([=[core.small_shard_1of2]=] "/repo/build/core" "--gtest_filter=Small_*" "--data=/d")\n'
          'set_tests_properties([=[core.small_shard_1of2]=] PROPERTIES ENVIRONMENT '
          '"GTEST_TOTAL_SHARDS=2;GTEST_SHARD_INDEX=1;PATH=/lib" LABELS "small" TIMEOUT "60")\n')


class _Programs:
    def __init__(self):
        self.calls = []

    def __call__(self, program, arguments, *, env=None, timeout=None):
        self.calls.append((program, arguments, env, timeout))
        return 0


def _run(files):
    programs = _Programs()
    profile = ModuleProfile(name="core", program="co", env_prefix="CO", root_marker="m")
    module = ModuleTests(profile=profile, project_root=lambda: Path("/repo"), console=RecordingConsole,
                         build_tree=lambda: K_TREE, run_ctest=None, run=None, run_program=programs)
    run_shard_cases(module, K_TREE, files, "core.small_shard_1of2", ["Small_A.One", "Small_A.Two"], K_REPORT)
    return programs.calls


def test_a_registered_shard_runs_its_cases_with_its_arguments_environment_and_timeout_but_no_sharding():
    calls = _run(MemoryFiles({K_TREE / "CTestTestfile.cmake": K_FILE}))
    assert calls == [("core", ["--gtest_filter=Small_A.One:Small_A.Two", f"--gtest_output=xml:{K_REPORT}",
                               "--data=/d"], {"PATH": "/lib"}, 60.0)]


def test_a_shard_the_tree_does_not_register_runs_its_cases_with_the_filter_alone():
    assert _run(MemoryFiles()) == [("core", ["--gtest_filter=Small_A.One:Small_A.Two",
                                             f"--gtest_output=xml:{K_REPORT}"], None, None)]
