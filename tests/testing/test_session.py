# test_session.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests running the tests of a tree and printing the budget line of the run."""

import pytest

from sushicore.profile import ModuleProfile
from sushicore.testing.labels import TestLabel, select_labels
from sushicore.testing.module_tests import ModuleTests, SanitizedTests
from sushicore.testing.session import run_tests

pytestmark = pytest.mark.small


class _Console:
    def __init__(self):
        self.said = []

    def info(self, text):
        self.said.append(("info", text))

    def warn(self, text):
        self.said.append(("warn", text))

    def error(self, text):
        self.said.append(("error", text))


class _Module:
    """Builds a ModuleTests over a tree below *root* and records what it is asked to run."""

    def __init__(self, root, ctest_code=0, writes_junit=True):
        self.root = root
        self.console = _Console()
        self.ctest_calls = []
        self.commands = []
        self.ctest_code = ctest_code
        self.writes_junit = writes_junit

    def tests(self, **extras):
        profile = ModuleProfile(name="sushitrack", program="st", env_prefix="ST", root_marker="m")
        return ModuleTests(profile=profile, project_root=lambda: self.root, console=lambda: self.console,
                           build_tree=lambda: self.root / "build", run_ctest=self._ctest, run=self._run,
                           **extras)

    def _ctest(self, tree, **keywords):
        self.ctest_calls.append(keywords)
        if self.writes_junit:
            keywords["output_junit"].write_text("<testsuite/>", encoding="utf-8")
        return self.ctest_code

    def _run(self, command, cwd):
        self.commands.append(command)
        return 0

    def carry_the_reader(self):
        (self.root / "tools" / "testing").mkdir(parents=True)
        (self.root / "tools" / "testing" / "test_budget.py").write_text("", encoding="utf-8")


def test_an_unfiltered_large_run_is_refused_before_anything_runs(tmp_path):
    module = _Module(tmp_path)
    code = run_tests(module.tests(), select_labels([TestLabel.LARGE]))
    assert (code, module.ctest_calls) == (2, [])
    assert "--all" in module.console.said[0][1]


def test_a_missing_tree_stops_the_run_and_names_the_build_command(tmp_path):
    module = _Module(tmp_path)
    assert run_tests(module.tests(), select_labels(None)) == 2
    assert "st build" in module.console.said[0][1]


def test_a_run_writes_a_junit_file_and_hands_it_to_the_reader(tmp_path):
    (tmp_path / "build").mkdir()
    module = _Module(tmp_path)
    module.carry_the_reader()
    assert run_tests(module.tests(), select_labels(None), name_filter="Rect") == 0
    junit = module.ctest_calls[0]["output_junit"]
    assert module.ctest_calls[0]["filter"] == "Rect" and junit.is_absolute()
    assert str(junit) in module.commands[0] and "partial" in module.commands[0]


def test_a_failing_run_keeps_its_code_and_still_prints_the_budget_line(tmp_path):
    (tmp_path / "build").mkdir()
    module = _Module(tmp_path, ctest_code=3)
    module.carry_the_reader()
    assert run_tests(module.tests(), select_labels(None)) == 3
    assert module.commands and "default" in module.commands[0]


def test_a_run_that_wrote_no_junit_file_skips_the_line_and_says_so(tmp_path):
    (tmp_path / "build").mkdir()
    module = _Module(tmp_path, writes_junit=False)
    module.carry_the_reader()
    assert run_tests(module.tests(), select_labels(None)) == 0
    assert module.commands == [] and module.console.said[-1][0] == "warn"


def test_a_sanitizer_is_built_and_its_tree_is_the_one_tested(tmp_path):
    (tmp_path / "asan").mkdir()
    module = _Module(tmp_path)
    built = []
    sanitized = SanitizedTests(names=("address",), build=lambda name: built.append(name) or 0,
                               tree=lambda name: tmp_path / "asan")
    assert run_tests(module.tests(sanitized=sanitized), select_labels(None), sanitizer="Address") == 0
    assert built == ["address"] and (tmp_path / "asan" / "Testing" / "junit.xml").is_file()


def test_a_failed_sanitizer_build_ends_the_run_with_its_code_and_runs_no_test(tmp_path):
    module = _Module(tmp_path)
    sanitized = SanitizedTests(names=("address",), build=lambda name: 4, tree=lambda name: tmp_path)
    assert run_tests(module.tests(sanitized=sanitized), select_labels(None), sanitizer="address") == 4
    assert module.ctest_calls == []


def test_a_module_without_the_sanitizer_or_the_suite_is_told_so_with_the_usage_code(tmp_path):
    module = _Module(tmp_path)
    assert run_tests(module.tests(), select_labels(None), sanitizer="address") == 2
    assert run_tests(module.tests(), select_labels(None), own_tests=True) == 2


def test_the_own_suite_runs_for_the_selection_and_skips_ctest(tmp_path):
    module = _Module(tmp_path)
    asked = []
    assert run_tests(module.tests(cli_tests=lambda selection: asked.append(selection) or 7),
                     select_labels([TestLabel.SMALL]), own_tests=True) == 7
    assert asked[0].sizes == (TestLabel.SMALL,) and module.ctest_calls == []
