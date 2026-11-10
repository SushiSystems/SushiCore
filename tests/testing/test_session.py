# test_session.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests running the tests of a tree and judging the run by its time limits."""

import json
from dataclasses import replace
from pathlib import Path

import pytest

from sushicore.console_memory import RecordingConsole
from sushicore.files_memory import MemoryFiles
from sushicore.proc_memory import RecordingRunner
from sushicore.memory_reading import K_RESERVE_MB
from sushicore.profile import ModuleProfile
from sushicore.testing.budget import K_UNUSABLE_TEXT
from sushicore.testing.labels import TestLabel, select_labels
from sushicore.testing.module_tests import ModuleTests, SanitizedTests
from sushicore.testing.session import run_tests

K_ROOT = Path("/repo")
K_BUILD = K_ROOT / "build"
K_ASAN = K_ROOT / "asan"
K_READER = K_ROOT / "tools" / "testing" / "test_budget.py"

pytestmark = pytest.mark.small


class _Module:
    """Builds a ModuleTests over an in-memory repository and records what it is asked to run."""

    def __init__(self, ctest_code=0, writes_junit=True, reader_code=0, trees=(K_BUILD,), junit_text="<testsuite/>",
                 extra_files=None, written_by_ctest=None):
        self.console = RecordingConsole()
        self.runner = RecordingRunner(self.console).script(exit_code=reader_code)
        self.files = MemoryFiles({tree / "CTestTestfile.cmake": "" for tree in trees})
        self.files.files.update(extra_files or {})
        self.junit_text = junit_text
        self.written_by_ctest = written_by_ctest or {}
        self.seen_in_results = []
        self.programs = []
        self.ctest_calls = []
        self.ctest_trees = []
        self.ctest_code = ctest_code
        self.writes_junit = writes_junit

    def tests(self, **extras):
        profile = ModuleProfile(name="sushitrack", program="st", env_prefix="ST", root_marker="m")
        return ModuleTests(profile=profile, project_root=lambda: K_ROOT, console=lambda: self.console,
                           build_tree=lambda: K_BUILD, run_ctest=self._ctest, run=self.runner.run,
                           **extras)

    def run(self, tests, selection, **options):
        options.setdefault("cpu_count", lambda: 8)
        options.setdefault("free_memory", lambda: 16384)
        return run_tests(tests, selection, files=self.files, **options)

    def carry_the_reader(self):
        self.files.write_text(K_READER, "")

    def reader_argv(self):
        return [command.argv for command in self.runner.commands]

    def _ctest(self, tree, **keywords):
        self.ctest_trees.append(tree)
        self.ctest_calls.append(keywords)
        self.seen_in_results.append(self.files.children(K_BUILD / "test_results" / "gtest"))
        if len(self.ctest_calls) == 1:
            self.files.files.update(self.written_by_ctest)
        if self.writes_junit and len(self.ctest_calls) == 1:
            self.files.write_text(keywords["output_junit"], self.junit_text)
        return self.ctest_code

    def program(self, name, arguments):
        self.programs.append((name, arguments))
        return 0


def test_an_unfiltered_large_run_is_refused_before_anything_runs():
    module = _Module()
    code = module.run(module.tests(), select_labels([TestLabel.LARGE]))
    assert (code, module.ctest_calls) == (2, [])
    assert "--all" in module.console.texts("error")[0]


def test_a_missing_tree_stops_the_run_and_names_the_build_command():
    module = _Module(trees=())
    assert module.run(module.tests(), select_labels(None)) == 2
    assert "st build" in module.console.texts("error")[0]


def test_a_run_hands_ctest_its_filter_and_an_absolute_junit_path():
    module = _Module()
    assert module.run(module.tests(), select_labels(None), name_filter="Rect") == 0
    assert module.ctest_calls[0]["filter"] == "Rect"
    assert module.ctest_calls[0]["output_junit"].is_absolute()


def test_a_run_hands_the_junit_file_and_its_scope_to_the_reader():
    module = _Module()
    module.carry_the_reader()
    assert module.run(module.tests(), select_labels(None), name_filter="Rect") == 0
    argv = module.reader_argv()[0]
    assert str(module.ctest_calls[0]["output_junit"]) in argv and "partial" in argv


def test_a_run_given_no_job_count_takes_one_per_core_and_prints_it():
    module = _Module()
    module.run(module.tests(), select_labels(None))
    assert module.ctest_calls[0]["jobs"] == 8
    assert any(text.startswith("Jobs: 8 (cores 8") for text in module.console.texts("info"))


def test_a_run_given_little_memory_takes_fewer_jobs_than_cores():
    module = _Module()
    module.run(module.tests(), select_labels(None), cpu_count=lambda: 32, free_memory=lambda: 5632)
    assert module.ctest_calls[0]["jobs"] == 4


def test_a_run_given_a_job_count_keeps_it_and_prints_no_choice():
    module = _Module()
    module.run(module.tests(), select_labels(None), jobs=3)
    assert module.ctest_calls[0]["jobs"] == 3
    assert not any(text.startswith("Jobs:") for text in module.console.texts("info"))


def test_a_failing_run_keeps_its_ctest_code():
    module = _Module(ctest_code=3)
    assert module.run(module.tests(), select_labels(None)) == 3


def test_a_failing_run_still_prints_the_budget_line():
    module = _Module(ctest_code=3)
    module.carry_the_reader()
    module.run(module.tests(), select_labels(None))
    assert "default" in module.reader_argv()[0]


def test_a_run_that_wrote_no_junit_file_skips_the_line_and_says_so():
    module = _Module(writes_junit=False)
    module.carry_the_reader()
    assert module.run(module.tests(), select_labels(None)) == 0
    assert module.reader_argv() == [] and len(module.console.texts("warn")) == 1


def test_a_reader_that_cannot_judge_a_passing_run_fails_it_and_says_so():
    module = _Module(reader_code=2)
    module.carry_the_reader()
    assert module.run(module.tests(), select_labels(None)) == 2
    assert module.console.texts("error") == [K_UNUSABLE_TEXT]


def test_a_passing_run_that_breaks_a_time_limit_fails_with_the_gate_code():
    module = _Module()
    module.runner.script(exit_code=1)
    module.carry_the_reader()
    assert module.run(module.tests(), select_labels(None)) == 1
    assert "--gate" in module.reader_argv()[1]
    assert module.console.texts("error") == ["The run broke a time limit."]


def test_a_failing_run_keeps_its_ctest_code_whatever_the_gate_says():
    module = _Module(ctest_code=8)
    module.runner.script(exit_code=1)
    module.carry_the_reader()
    assert module.run(module.tests(), select_labels(None)) == 8


def test_a_run_hands_ctest_a_resource_file_with_one_accelerator_slot():
    module = _Module()
    module.run(module.tests(), select_labels(None))
    spec = module.ctest_calls[0]["resource_spec_file"]
    assert spec == K_BUILD / "Testing" / "resources.json"
    assert json.loads(module.files.read_text(spec))["local"] == [{"gpus": [{"id": "0", "slots": 1}]}]


def test_a_sanitizer_is_built_and_its_tree_is_the_one_tested():
    module = _Module(trees=(K_ASAN,))
    built = []
    sanitized = SanitizedTests(names=("address",), build=lambda name: built.append(name) or 0,
                               tree=lambda name: K_ASAN)
    assert module.run(module.tests(sanitized=sanitized), select_labels(None), sanitizer="Address") == 0
    assert built == ["address"] and module.ctest_trees == [K_ASAN]


def test_a_failed_sanitizer_build_ends_the_run_with_its_code_and_runs_no_test():
    module = _Module()
    sanitized = SanitizedTests(names=("address",), build=lambda name: 4, tree=lambda name: K_ROOT)
    assert module.run(module.tests(sanitized=sanitized), select_labels(None), sanitizer="address") == 4
    assert module.ctest_calls == []


def test_a_module_without_the_sanitizer_is_told_so_with_the_usage_code():
    module = _Module()
    assert module.run(module.tests(), select_labels(None), sanitizer="address") == 2


def test_a_module_without_a_suite_of_its_own_is_told_so_with_the_usage_code():
    module = _Module()
    assert module.run(module.tests(), select_labels(None), own_tests=True) == 2


def test_the_own_suite_refuses_an_option_it_would_drop():
    module = _Module()
    own = module.tests(cli_tests=lambda selection: 0)
    assert module.run(own, select_labels(None), own_tests=True, name_filter="Rect", jobs=2) == 2
    assert "--filter, --jobs" in module.console.texts("error")[-1]


def test_a_sanitizer_matches_the_module_names_without_regard_to_case():
    module = _Module(trees=(K_ASAN,))
    sanitized = SanitizedTests(names=("Address",), build=lambda name: 0 if name == "Address" else 9,
                               tree=lambda name: K_ASAN)
    assert module.run(module.tests(sanitized=sanitized), select_labels(None), sanitizer="ADDRESS") == 0


def test_the_own_suite_runs_for_the_selection_and_skips_ctest():
    module = _Module()
    asked = []
    assert module.run(module.tests(cli_tests=lambda selection: asked.append(selection) or 7),
                      select_labels([TestLabel.SMALL]), own_tests=True) == 7
    assert asked[0].sizes == (TestLabel.SMALL,) and module.ctest_calls == []


@pytest.mark.parametrize("rebuilt, flagged", [(None, True), (lambda tree: False, True), (lambda tree: True, False)])
def test_a_run_is_marked_not_rebuilt_unless_the_module_says_it_rebuilt(rebuilt, flagged):
    module = _Module()
    module.carry_the_reader()
    assert module.run(module.tests(rebuilt=rebuilt), select_labels(None)) == 0
    assert ("--not-rebuilt" in module.reader_argv()[0]) is flagged


def test_a_sanitizer_run_is_rebuilt_because_it_builds_its_tree_first():
    module = _Module(trees=(K_ASAN,))
    module.carry_the_reader()
    sanitized = SanitizedTests(names=("address",), build=lambda name: 0, tree=lambda name: K_ASAN)
    assert module.run(module.tests(sanitized=sanitized), select_labels(None), sanitizer="address") == 0
    assert "--not-rebuilt" not in module.reader_argv()[0]


def test_a_run_shuffles_with_the_given_seed():
    module = _Module()
    assert module.run(module.tests(), select_labels(None), seed=4242) == 0
    assert module.ctest_calls[0]["shuffle_seed"] == 4242


def test_a_run_prints_the_seed_it_shuffles_with():
    module = _Module()
    module.run(module.tests(), select_labels(None), seed=4242)
    assert any("4242" in text for text in module.console.texts("info"))


def test_a_run_without_a_seed_draws_one_in_the_range_gtest_accepts():
    module = _Module()
    bounds = []

    def draw(low, high):
        bounds.append((low, high))
        return 77

    assert module.run(module.tests(), select_labels(None), seed_source=draw) == 0
    assert bounds == [(1, 99999)] and module.ctest_calls[0]["shuffle_seed"] == 77


def test_a_run_that_turns_the_shuffle_off_gives_ctest_no_seed():
    module = _Module()
    assert module.run(module.tests(), select_labels(None), shuffle=False) == 0
    assert "shuffle_seed" not in module.ctest_calls[0]


def test_a_ctest_call_without_the_shuffle_keyword_still_runs_and_the_run_says_so():
    module = _Module()
    seen = []

    def old_ctest(tree, label_regex, exclude_label_regex, filter, repeat, jobs, output_junit):
        seen.append(filter)
        return 0

    tests = replace(module.tests(), run_ctest=old_ctest)
    assert module.run(tests, select_labels(None), name_filter="Rect") == 0
    assert seen == ["Rect"]
    assert [text for text in module.console.texts("warn") if "shuffle" in text] == [
        "This CLI's CTest call cannot take a shuffle seed, so the tests run in their given order."]
    assert [text for text in module.console.texts("warn") if "resource" in text] == [
        "This CLI's CTest call cannot take a resource file, so device shards may share a device."]


K_GTEST_DIR = K_BUILD / "test_results" / "gtest"
K_SHARD = "core.small_shard_0of1"
K_SHARDED = {K_BUILD / "CTestTestfile.cmake": f'add_test([=[{K_SHARD}]=] "/repo/build/core")\n'}
K_FAILED_SHARD_JUNIT = f'<testsuite><testcase name="{K_SHARD}" status="fail"><failure/></testcase></testsuite>'
K_ONE_FAILING_CASE = (
    '<testsuites><testsuite><testcase name="One" classname="Small_A"><failure/></testcase></testsuite></testsuites>')


def test_a_run_clears_the_shard_results_of_the_run_before_it_and_gives_the_reader_the_folder_after():
    stale = K_GTEST_DIR / "old.xml"
    module = _Module(extra_files={stale: "<testsuites/>"})
    module.carry_the_reader()
    module.files.write_text(K_GTEST_DIR / "fresh.xml", "<testsuites/>")
    module.run(module.tests(), select_labels(None))
    assert module.seen_in_results == [[]]
    assert "--cases" not in module.reader_argv()[0]


def test_a_run_that_leaves_shard_results_gives_the_reader_their_folder():
    module = _Module()
    module.carry_the_reader()
    original = module._ctest

    def writing_ctest(tree, **keywords):
        module.files.write_text(K_GTEST_DIR / "shard.xml", "<testsuites/>")
        return original(tree, **keywords)

    tests = replace(module.tests(), run_ctest=writing_ctest)
    module.run(tests, select_labels(None))
    argv = module.reader_argv()[0]
    assert argv[argv.index("--cases") + 1] == str(K_GTEST_DIR)


def test_a_failed_shard_is_rerun_by_filter_on_its_program_and_the_reader_gets_the_rerun_folder():
    module = _Module(ctest_code=1, junit_text=K_FAILED_SHARD_JUNIT,
                     extra_files=K_SHARDED,
                     written_by_ctest={K_GTEST_DIR / f"{K_SHARD}.xml": K_ONE_FAILING_CASE})
    module.carry_the_reader()
    assert module.run(module.tests(run_program=module.program), select_labels(None)) == 1
    assert module.programs[0][0] == "core" and module.programs[0][1][0] == "--gtest_filter=Small_A.One"
    argv = module.reader_argv()[0]
    assert argv[argv.index("--rerun") + 1] == str(K_BUILD / "test_results" / "rerun")


def test_a_case_that_passes_alone_is_said_to_be_flaky_and_the_code_stays_ctests():
    module = _Module(ctest_code=1, junit_text=K_FAILED_SHARD_JUNIT,
                     extra_files=K_SHARDED,
                     written_by_ctest={K_GTEST_DIR / f"{K_SHARD}.xml": K_ONE_FAILING_CASE})
    assert module.run(module.tests(run_program=module.program), select_labels(None)) == 1
    assert any("Flaky" in text and "Small_A.One" in text for text in module.console.texts("warn"))


def test_a_failed_test_of_an_unsharded_build_is_rerun_by_its_ctest_name():
    junit = '<testsuite><testcase name="Small_A.One" status="fail"><failure/></testcase></testsuite>'
    module = _Module(ctest_code=1, junit_text=junit)
    module.run(module.tests(run_program=module.program), select_labels(None))
    assert module.programs == [] and module.ctest_calls[1]["filter"] == r"^(Small_A\.One)$"


def test_a_passing_run_reruns_nothing():
    module = _Module(junit_text=K_FAILED_SHARD_JUNIT, extra_files=K_SHARDED)
    module.run(module.tests(run_program=module.program), select_labels(None))
    assert len(module.ctest_calls) == 1 and module.programs == []


def test_a_filter_over_a_sharded_build_reaches_every_shard_as_the_gtest_filter_and_not_as_a_name_pattern():
    module = _Module(extra_files=K_SHARDED)
    module.run(module.tests(), select_labels(None), name_filter="Small_A.*")
    call = module.ctest_calls[0]
    assert (call["gtest_filter"], call["filter"]) == ("Small_A.*", None)


def test_a_filter_over_an_unsharded_build_stays_a_ctest_name_pattern():
    module = _Module()
    module.run(module.tests(), select_labels(None), name_filter="Rect")
    call = module.ctest_calls[0]
    assert (call["filter"], "gtest_filter" in call) == ("Rect", False)


def test_a_sharded_build_whose_ctest_call_cannot_take_a_gtest_filter_keeps_the_name_pattern_and_says_so():
    module = _Module(extra_files=K_SHARDED)
    seen = []

    def old_ctest(tree, label_regex, exclude_label_regex, filter, repeat, jobs, output_junit, shuffle_seed):
        seen.append(filter)
        return 0

    module.run(replace(module.tests(), run_ctest=old_ctest), select_labels(None), name_filter="Rect")
    assert seen == ["Rect"] and any("GoogleTest filter" in text for text in module.console.texts("warn"))


def test_a_run_of_small_tests_alone_takes_every_core_where_medium_tests_would_not_fit():
    module = _Module()
    module.run(module.tests(), select_labels([TestLabel.SMALL]), free_memory=lambda: K_RESERVE_MB + 2 * 1024 + 10)
    module.run(module.tests(), select_labels(None), free_memory=lambda: K_RESERVE_MB + 2 * 1024 + 10)
    assert [call["jobs"] for call in module.ctest_calls] == [8, 2]


def test_a_filter_over_shards_of_a_module_with_run_program_runs_the_narrowed_shards_and_not_ctest():
    sharded = ('add_test([=[core.small_shard_0of1]=] "/repo/build/core" "--gtest_filter=Small_*")\n'
               'set_tests_properties([=[core.small_shard_0of1]=] PROPERTIES ENVIRONMENT '
               '"GTEST_TOTAL_SHARDS=1;GTEST_SHARD_INDEX=0" LABELS "small" TIMEOUT "60")\n')
    module = _Module(extra_files={K_BUILD / "CTestTestfile.cmake": sharded})
    calls = []

    def run_program(program, arguments, *, env=None, timeout=None):
        calls.append((program, arguments[0], env["GTEST_SHARD_INDEX"], timeout))
        return 0

    assert module.run(module.tests(run_program=run_program), select_labels(None), name_filter="Small_A.*") == 0
    assert calls == [("core", "--gtest_filter=Small_A.*", "0", 60.0)] and module.ctest_calls == []
