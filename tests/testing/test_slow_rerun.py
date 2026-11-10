# test_slow_rerun.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests rerunning alone the tests a run found over their time limit."""

from pathlib import Path

import pytest

from sushicore.console_memory import RecordingConsole
from sushicore.files_memory import MemoryFiles
from sushicore.profile import ModuleProfile
from sushicore.testing.module_tests import ModuleTests
from sushicore.testing.slow_rerun import SlowTestRerun

pytestmark = pytest.mark.small

K_TREE = Path("/repo/build")
K_CASES = K_TREE / "test_results" / "gtest"
K_SLOW = K_TREE / "test_results" / "slow"


def _gtest(*names):
    rows = "".join(f'<testcase classname="{name.split(".")[0]}" name="{name.split(".")[1]}" time="1"/>' for name in names)
    return f"<testsuites><testsuite>{rows}</testsuite></testsuites>"


class _Module:
    def __init__(self, files, with_program=True):
        self.programs = []
        self.ctest = []
        self.files = files
        profile = ModuleProfile(name="core", program="co", env_prefix="CO", root_marker="m")
        self.tests = ModuleTests(profile=profile, project_root=lambda: Path("/repo"), console=RecordingConsole,
                                 build_tree=lambda: K_TREE, run_ctest=self._ctest, run=None,
                                 run_program=self._program if with_program else None)

    def _program(self, name, arguments, **options):
        self.programs.append((name, arguments))
        return 0

    def _ctest(self, tree, **keywords):
        self.ctest.append(keywords)
        self.files.write_text(keywords["output_junit"], "<testsuite/>")
        return 0


def test_the_cases_of_one_shard_rerun_together_through_its_program_into_the_slow_folder():
    files = MemoryFiles({K_CASES / "core.small_shard_1of2.xml": _gtest("Small_A.One", "Small_A.Two"),
                         K_CASES / "core.small_shard_2of2.xml": _gtest("Small_B.Three")})
    module = _Module(files)
    written = SlowTestRerun(module.tests, K_TREE, files).rerun(["Small_A.One", "Small_A.Two"])
    assert written == (K_SLOW,)
    assert module.programs == [("core", ["--gtest_filter=Small_A.One:Small_A.Two",
                                         f"--gtest_output=xml:{K_SLOW / 'core.small_shard_1of2.xml'}"])]


def test_a_test_of_no_shard_reruns_through_ctest_with_one_job():
    files = MemoryFiles()
    module = _Module(files)
    written = SlowTestRerun(module.tests, K_TREE, files).rerun(["test_parse.small"])
    assert written == (K_TREE / "Testing" / "slow_junit.xml",)
    assert (module.ctest[0]["filter"], module.ctest[0]["jobs"]) == ("^(test_parse\.small)$", 1)


def test_a_shard_case_of_a_module_that_cannot_run_its_program_is_not_rerun():
    files = MemoryFiles({K_CASES / "core.small_shard_1of1.xml": _gtest("Small_A.One")})
    module = _Module(files, with_program=False)
    assert SlowTestRerun(module.tests, K_TREE, files).rerun(["Small_A.One"]) == ()
    assert (module.programs, module.ctest) == ([], [])


def test_nothing_to_rerun_runs_nothing():
    files = MemoryFiles()
    module = _Module(files)
    assert SlowTestRerun(module.tests, K_TREE, files).rerun([]) == ()
