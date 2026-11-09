# test_budget.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests what a run is judged as and the call of the budget reader."""

from pathlib import Path

import pytest

from sushicore.console_memory import RecordingConsole
from sushicore.files_memory import MemoryFiles
from sushicore.profile import ModuleProfile
from sushicore.proc_memory import RecordingRunner
from sushicore.testing.budget import print_budget, reader_command, scope_of
from sushicore.testing.labels import TestLabel, large_needs_a_filter, select_labels
from sushicore.testing.module_tests import ModuleTests

pytestmark = pytest.mark.small

K_ROOT = Path("/repo")
K_JUNIT = K_ROOT / "build" / "Testing" / "junit.xml"
K_READER = K_ROOT / "tools" / "testing" / "test_budget.py"
K_EXEMPTIONS = K_ROOT / "tests" / "budget_exemptions.toml"


def _module(console, runner):
    profile = ModuleProfile(name="sushitrack", program="st", env_prefix="ST", root_marker="m")
    return ModuleTests(profile=profile, project_root=lambda: K_ROOT, console=lambda: console,
                       build_tree=lambda: K_ROOT / "build", run_ctest=lambda tree, **keywords: 0,
                       run=runner.run)


@pytest.mark.parametrize("labels, filtered, every_size, repeated, scope", [
    (None, False, False, False, "default"),
    (None, True, False, False, "partial"),
    (None, False, False, True, "partial"),
    ([TestLabel.SMALL], False, False, False, "partial"),
    (None, False, True, False, "large"),
    ([TestLabel.LARGE], True, False, False, "partial"),
])
def test_a_run_is_default_only_when_nothing_narrowed_it(labels, filtered, every_size, repeated, scope):
    selection = select_labels(labels, every_size=every_size)
    assert scope_of(selection, filtered=filtered, every_size=every_size, repeated=repeated) == scope


@pytest.mark.parametrize("labels, filtered, every_size, refused", [
    ([TestLabel.LARGE], False, False, True),
    ([TestLabel.LARGE], True, False, False),
    (None, False, True, False),
    (None, False, False, False),
])
def test_the_large_tests_start_only_when_something_narrows_them(labels, filtered, every_size, refused):
    selection = select_labels(labels, every_size=every_size)
    assert large_needs_a_filter(selection, filtered=filtered, every_size=every_size) is refused


def test_the_reader_command_is_none_where_the_repository_carries_no_reader():
    assert reader_command(K_ROOT, K_JUNIT, "default", 3.0, files=MemoryFiles()) is None


def test_the_reader_command_names_the_junit_file_the_scope_and_the_rounded_wall_time():
    files = MemoryFiles({K_READER: "", K_EXEMPTIONS: ""})
    command = reader_command(K_ROOT, K_JUNIT, "partial", 3.04, files=files)
    assert command[1:] == [str(K_READER), str(K_JUNIT), "--scope", "partial", "--wall", "3.0",
                           "--root", str(K_ROOT), "--exemptions", str(K_EXEMPTIONS)]


def test_the_reader_command_marks_a_run_that_did_not_rebuild():
    files = MemoryFiles({K_READER: ""})
    assert "--not-rebuilt" in reader_command(K_ROOT, K_JUNIT, "default", 3.0, rebuilt=False, files=files)
    assert "--not-rebuilt" not in reader_command(K_ROOT, K_JUNIT, "default", 3.0, files=files)


def test_print_budget_warns_and_leaves_the_run_unchanged_when_the_reader_fails():
    console = RecordingConsole()
    runner = RecordingRunner(console).script(exit_code=1)
    files = MemoryFiles({K_READER: "", K_JUNIT: "<testsuite/>"})
    print_budget(_module(console, runner), K_JUNIT, "default", 3.0, files=files)
    assert console.texts("warn") == ["The budget reader failed; the run's own result is unchanged."]


def test_the_reader_command_hands_the_shard_folder_and_the_rerun_results_to_the_reader():
    files = MemoryFiles({K_READER: ""})
    command = reader_command(K_ROOT, K_JUNIT, "default", 3.0, files=files,
                             cases=K_ROOT / "build" / "cases", rerun=K_ROOT / "build" / "rerun")
    assert command[-4:] == ["--cases", str(K_ROOT / "build" / "cases"), "--rerun", str(K_ROOT / "build" / "rerun")]


def test_print_budget_leaves_out_a_shard_folder_that_does_not_exist():
    console = RecordingConsole()
    runner = RecordingRunner(console)
    files = MemoryFiles({K_READER: "", K_JUNIT: "<testsuite/>"})
    print_budget(_module(console, runner), K_JUNIT, "default", 3.0, files=files, cases=K_ROOT / "build" / "cases")
    assert "--cases" not in runner.commands[0].argv


def test_print_budget_hands_the_reader_the_shard_folder_that_exists():
    console = RecordingConsole()
    runner = RecordingRunner(console)
    cases = K_ROOT / "build" / "cases"
    files = MemoryFiles({K_READER: "", K_JUNIT: "<testsuite/>", cases / "a.xml": "<testsuites/>"})
    print_budget(_module(console, runner), K_JUNIT, "default", 3.0, files=files, cases=cases)
    assert runner.commands[0].argv[-2:] == ("--cases", str(cases))
