# test_rerun.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests rerunning the failed tests of a run once, alone."""

from pathlib import Path

import pytest

from sushicore.console_memory import RecordingConsole
from sushicore.files_memory import MemoryFiles
from sushicore.profile import ModuleProfile
from sushicore.testing.module_tests import ModuleTests
from sushicore.testing.rerun import FailedTestRerun

pytestmark = pytest.mark.small

K_TREE = Path("/repo/build")
K_SHARD = "core.small_shard_1of2"
K_GTEST = K_TREE / "test_results" / "gtest" / f"{K_SHARD}.xml"
K_RERUN = K_TREE / "test_results" / "rerun"
K_RERUN_JUNIT = K_TREE / "Testing" / "rerun_junit.xml"
K_TWO_FAILURES = (
    '<testsuites><testsuite>'
    '<testcase name="Ok" classname="Small_A"/>'
    '<testcase name="One" classname="Small_A"><failure/></testcase>'
    '<testcase name="Two/1" classname="Rows/Small_B"><failure/></testcase>'
    "</testsuite></testsuites>")


def _junit(*failed):
    rows = "".join(f'<testcase name="{name}" status="fail"><failure/></testcase>' for name in failed)
    return f"<testsuite>{rows}</testsuite>"


class _Fakes:
    """Builds a ModuleTests whose program and CTest call answer the exit codes and the files given."""

    def __init__(self, program_code=0, ctest_failures=(), files=None):
        self.console = RecordingConsole()
        self.files = MemoryFiles(files or {})
        self.programs = []
        self.ctests = []
        self.program_code = program_code
        self.ctest_failures = ctest_failures

    def tests(self, *, with_program=True):
        profile = ModuleProfile(name="sushitrack", program="st", env_prefix="ST", root_marker="m")
        return ModuleTests(profile=profile, project_root=lambda: Path("/repo"), console=lambda: self.console,
                           build_tree=lambda: K_TREE, run_ctest=self._ctest, run=lambda command, cwd: 0,
                           run_program=self._program if with_program else None)

    def rerun(self, failed, **options):
        return FailedTestRerun(self.tests(**options), K_TREE, self.files).rerun(failed)

    def _program(self, program, arguments):
        self.programs.append((program, arguments))
        return self.program_code

    def _ctest(self, tree, **keywords):
        self.ctests.append(keywords)
        self.files.write_text(keywords["output_junit"], _junit(*self.ctest_failures))
        return 1 if self.ctest_failures else 0


def test_a_failed_shard_reruns_only_its_failing_cases_by_filter_on_its_program():
    fakes = _Fakes(files={K_GTEST: K_TWO_FAILURES})
    fakes.rerun([K_SHARD])
    assert fakes.programs == [("core", ["--gtest_filter=Small_A.One:Rows/Small_B.Two/1",
                                        f"--gtest_output=xml:{K_RERUN / (K_SHARD + '.xml')}"])]
    assert fakes.ctests == []


def test_failing_cases_that_pass_alone_are_flaky_and_the_rerun_folder_goes_to_the_reader():
    fakes = _Fakes(program_code=0, files={K_GTEST: K_TWO_FAILURES})
    outcome = fakes.rerun([K_SHARD])
    assert (outcome.results, outcome.flaky, outcome.failing) == (K_RERUN, ("Small_A.One", "Rows/Small_B.Two/1"), ())


def test_failing_cases_that_fail_alone_again_are_failing_and_not_flaky():
    fakes = _Fakes(program_code=1, files={K_GTEST: K_TWO_FAILURES})
    outcome = fakes.rerun([K_SHARD])
    assert (outcome.flaky, outcome.failing) == ((), ("Small_A.One", "Rows/Small_B.Two/1"))


def test_a_failed_test_that_is_no_shard_reruns_whole_by_ctest_name_and_its_junit_goes_to_the_reader():
    fakes = _Fakes(ctest_failures=("Small_A.One",))
    outcome = fakes.rerun(["Small_A.One", "Small_A.Two"])
    assert fakes.ctests[0]["filter"] == r"^(Small_A\.One|Small_A\.Two)$"
    assert (fakes.programs, outcome.results, outcome.flaky, outcome.failing) == (
        [], K_RERUN_JUNIT, ("Small_A.Two",), ("Small_A.One",))


def test_a_ctest_rerun_runs_one_job_over_no_label_and_no_repeat():
    fakes = _Fakes()
    fakes.rerun(["Small_A.One"])
    call = fakes.ctests[0]
    assert (call["jobs"], call["label_regex"], call["exclude_label_regex"], call["repeat"]) == (1, None, None, 0)


def test_a_shard_that_wrote_no_result_file_reruns_whole_by_ctest():
    fakes = _Fakes()
    fakes.rerun([K_SHARD])
    assert fakes.programs == [] and fakes.ctests[0]["filter"] == r"^(core\.small_shard_1of2)$"


def test_a_module_that_cannot_run_its_program_reruns_a_shard_whole_by_ctest():
    fakes = _Fakes(files={K_GTEST: K_TWO_FAILURES})
    fakes.rerun([K_SHARD], with_program=False)
    assert fakes.programs == [] and len(fakes.ctests) == 1


def test_a_shard_file_that_is_not_xml_reruns_the_shard_whole_by_ctest():
    fakes = _Fakes(files={K_GTEST: "<testsuites"})
    fakes.rerun([K_SHARD])
    assert fakes.programs == [] and len(fakes.ctests) == 1


def test_the_results_of_an_earlier_rerun_are_cleared_first():
    stale = K_RERUN / "old.xml"
    fakes = _Fakes(files={K_GTEST: K_TWO_FAILURES, stale: "<testsuites/>"})
    fakes.rerun([K_SHARD])
    assert not fakes.files.is_file(stale)


def test_no_failed_test_means_nothing_is_rerun():
    fakes = _Fakes()
    outcome = fakes.rerun([])
    assert (outcome.results, fakes.programs, fakes.ctests) == (None, [], [])
