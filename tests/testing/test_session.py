# test_session.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests running the tests of a tree and printing the budget line of the run."""

from dataclasses import replace
from pathlib import Path

import pytest

from sushicore.console_memory import RecordingConsole
from sushicore.files_memory import MemoryFiles
from sushicore.proc_memory import RecordingRunner
from sushicore.profile import ModuleProfile
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

    def __init__(self, ctest_code=0, writes_junit=True, reader_code=0, trees=(K_BUILD,)):
        self.console = RecordingConsole()
        self.runner = RecordingRunner(self.console).script(exit_code=reader_code)
        self.files = MemoryFiles({tree / "CTestTestfile.cmake": "" for tree in trees})
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
        return run_tests(tests, selection, files=self.files, **options)

    def carry_the_reader(self):
        self.files.write_text(K_READER, "")

    def reader_argv(self):
        return [command.argv for command in self.runner.commands]

    def _ctest(self, tree, **keywords):
        self.ctest_trees.append(tree)
        self.ctest_calls.append(keywords)
        if self.writes_junit:
            self.files.write_text(keywords["output_junit"], "<testsuite/>")
        return self.ctest_code


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


def test_a_failing_reader_is_said_in_a_warning_and_leaves_the_code():
    module = _Module(reader_code=1)
    module.carry_the_reader()
    assert module.run(module.tests(), select_labels(None)) == 0
    assert module.console.texts("warn") == ["The budget reader failed; the run's own result is unchanged."]


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
    assert seen == ["Rect"] and len(module.console.texts("warn")) == 1
