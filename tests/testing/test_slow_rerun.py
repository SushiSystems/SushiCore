# test_slow_rerun.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests rerunning alone the tests a run found over their time limit."""

from pathlib import Path

import pytest

from sushicore.console_memory import RecordingConsole
from sushicore.files import DiskFiles
from sushicore.files_memory import MemoryFiles
from sushicore.profile import ModuleProfile
from sushicore.testing.module_tests import ModuleTests
from sushicore.testing.slow_rerun import SlowTestRerun, slow_results_folder


K_TREE = Path("/repo/build")
K_CASES = K_TREE / "test_results" / "gtest"
K_SLOW = K_TREE / "test_results" / "slow"


def _gtest(*names):
    rows = "".join(f'<testcase classname="{name.split(".")[0]}" name="{name.split(".")[1]}" time="1"/>' for name in names)
    return f"<testsuites><testsuite>{rows}</testsuite></testsuites>"


class _Module:
    def __init__(self, files, with_program=True, writes_result=True):
        self.programs = []
        self.writes_result = writes_result
        self.console = RecordingConsole()
        self.ctest = []
        self.files = files
        profile = ModuleProfile(name="core", program="co", env_prefix="CO", root_marker="m")
        self.tests = ModuleTests(profile=profile, project_root=lambda: Path("/repo"), console=lambda: self.console,
                                 build_tree=lambda: K_TREE, run_ctest=self._ctest, run=None,
                                 run_program=self._program if with_program else None)

    def _program(self, name, arguments, **options):
        self.programs.append((name, arguments))
        if self.writes_result:
            self.files.write_text(Path(arguments[1].split("xml:", 1)[1]), "<testsuites/>")
        return 0

    def _ctest(self, tree, **keywords):
        self.ctest.append(keywords)
        self.files.write_text(keywords["output_junit"], "<testsuite/>")
        return 0


@pytest.mark.small
def test_the_cases_of_one_shard_rerun_together_through_its_program_into_the_slow_folder():
    files = MemoryFiles({K_CASES / "core.small_shard_1of2.xml": _gtest("Small_A.One", "Small_A.Two"),
                         K_CASES / "core.small_shard_2of2.xml": _gtest("Small_B.Three")})
    module = _Module(files)
    written = SlowTestRerun(module.tests, K_TREE, files).rerun(["Small_A.One", "Small_A.Two"])
    assert written == (K_SLOW,)
    assert module.programs == [("core", ["--gtest_filter=Small_A.One:Small_A.Two",
                                         f"--gtest_output=xml:{K_SLOW / 'core.small_shard_1of2.xml'}"])]


@pytest.mark.small
def test_a_test_of_no_shard_reruns_through_ctest_with_one_job():
    files = MemoryFiles()
    module = _Module(files)
    written = SlowTestRerun(module.tests, K_TREE, files).rerun(["test_parse.small"])
    assert written == (K_TREE / "Testing" / "slow_junit.xml",)
    assert (module.ctest[0]["filter"], module.ctest[0]["jobs"]) == (r"^(test_parse\.small)$", 1)


@pytest.mark.small
def test_a_shard_case_of_a_module_that_cannot_run_its_program_is_not_rerun():
    files = MemoryFiles({K_CASES / "core.small_shard_1of1.xml": _gtest("Small_A.One")})
    module = _Module(files, with_program=False)
    assert SlowTestRerun(module.tests, K_TREE, files).rerun(["Small_A.One"]) == ()
    assert (module.programs, module.ctest) == ([], [])


@pytest.mark.small
def test_nothing_to_rerun_runs_nothing():
    files = MemoryFiles()
    module = _Module(files)
    assert SlowTestRerun(module.tests, K_TREE, files).rerun([]) == ()


@pytest.mark.small
def test_a_rerun_that_wrote_no_result_is_said_and_names_no_folder():
    files = MemoryFiles({K_CASES / "core.small_shard_1of1.xml": _gtest("Small_A.One")})
    module = _Module(files, writes_result=False)
    written = SlowTestRerun(module.tests, K_TREE, files).rerun(["Small_A.One"])
    assert written == ()
    warnings = [call.text for call in module.console.calls if call.kind == "warn"]
    assert len(warnings) == 1 and "core.small_shard_1of1" in warnings[0] and "exited 0" in warnings[0]



@pytest.mark.medium
def test_a_failed_rerun_names_no_folder_left_from_an_earlier_run(tmp_path):
    files = DiskFiles()
    cases = tmp_path / K_CASES.relative_to(K_TREE) / "core.small_shard_1of1.xml"
    cases.parent.mkdir(parents=True)
    cases.write_text(_gtest("Small_A.One"), encoding="utf-8")
    stale = slow_results_folder(tmp_path) / "old.xml"
    stale.parent.mkdir(parents=True)
    stale.write_text("<testsuites/>", encoding="utf-8")
    module = _Module(files, writes_result=False)
    assert SlowTestRerun(module.tests, tmp_path, files).rerun(["Small_A.One"]) == ()
