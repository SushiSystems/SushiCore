# test_budget.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests what a run is judged as, the calls of the budget reader and the gate."""

from pathlib import Path

import pytest

from sushicore.console_memory import RecordingConsole
from sushicore.files_memory import MemoryFiles
from sushicore.profile import ModuleProfile
from sushicore.testing.budget import K_UNUSABLE_TEXT, judge_run, program_map, reader_command, scope_of
from sushicore.testing.labels import TestLabel, large_needs_a_filter, select_labels
from sushicore.testing.module_tests import ModuleTests

pytestmark = pytest.mark.small

K_ROOT = Path("/repo")
K_TREE = K_ROOT / "build"
K_JUNIT = K_TREE / "Testing" / "junit.xml"
K_CASES = K_TREE / "test_results" / "gtest"
K_READER = K_ROOT / "tools" / "testing" / "test_budget.py"
K_EXEMPTIONS = K_ROOT / "tests" / "budget_exemptions.toml"


def _gtest(suite: str, case: str) -> str:
    return f'<testsuites><testsuite><testcase classname="{suite}" name="{case}" time="0.5"/></testsuite></testsuites>'


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


def test_the_reader_command_hands_on_every_rerun_the_programs_the_gate_and_the_listing():
    files = MemoryFiles({K_READER: ""})
    command = reader_command(K_ROOT, K_JUNIT, "default", 3.0, files=files, cases=K_CASES,
                             reruns=(K_ROOT / "a", K_ROOT / "b"), programs=K_ROOT / "p.json", gate=True,
                             list_over=K_ROOT / "over.txt")
    assert command[9:] == ["--cases", str(K_CASES), "--rerun", str(K_ROOT / "a"), "--rerun", str(K_ROOT / "b"),
                           "--programs", str(K_ROOT / "p.json"), "--gate", "--list-over", str(K_ROOT / "over.txt")]


def test_the_program_map_names_the_program_of_each_suite_part_from_the_shard_files():
    files = MemoryFiles({K_CASES / "core_tests.small_shard_1of2.xml": _gtest("Small_A", "One"),
                         K_CASES / "io_tests.medium_shard_1of1.xml": _gtest("Inst/Medium_B", "Two/0"),
                         K_CASES / "notes.txt": "x"})
    assert program_map(K_CASES, files) == {"Small_A": "core_tests", "Inst": "io_tests", "Medium_B": "io_tests"}


class _Reader:
    """Stands in for the budget reader: writes the scripted listing and answers the scripted exit codes."""

    def __init__(self, files: MemoryFiles, over: tuple[str, ...], codes: tuple[int, ...]) -> None:
        self.files = files
        self.over = over
        self.codes = list(codes)
        self.commands: list[list[str]] = []

    def __call__(self, command: list[str], folder: Path) -> int:
        self.commands.append(list(command))
        if "--list-over" in command:
            self.files.write_text(Path(command[command.index("--list-over") + 1]), "".join(f"{n}\n" for n in self.over))
        return self.codes.pop(0) if self.codes else 0


def _judge(files: MemoryFiles, reader: _Reader, console: RecordingConsole, run_program=None, **keywords) -> int:
    profile = ModuleProfile(name="sushitrack", program="st", env_prefix="ST", root_marker="m")
    module = ModuleTests(profile=profile, project_root=lambda: K_ROOT, console=lambda: console,
                         build_tree=lambda: K_TREE, run_ctest=lambda tree, **options: 0, run=reader,
                         run_program=run_program)
    return judge_run(module, K_TREE, K_JUNIT, "default", 3.0, files=files, **keywords)


def test_a_run_within_its_limits_lists_nothing_reruns_nothing_and_passes_through_the_gate():
    console = RecordingConsole()
    files = MemoryFiles({K_READER: "", K_JUNIT: "<testsuite/>"})
    reader = _Reader(files, over=(), codes=(0, 0))
    assert _judge(files, reader, console) == 0
    assert "--list-over" in reader.commands[0] and "--gate" not in reader.commands[0]
    assert "--gate" in reader.commands[1] and "--rerun" not in reader.commands[1]


def test_a_shard_case_over_its_limit_reruns_alone_and_the_gate_judges_that_time():
    console = RecordingConsole()
    files = MemoryFiles({K_READER: "", K_JUNIT: "<testsuite/>",
                         K_CASES / "core_tests.small_shard_1of1.xml": _gtest("Small_A", "Slow")})
    reader = _Reader(files, over=("Small_A.Slow",), codes=(0, 1))
    calls = []
    code = _judge(files, reader, console, run_program=lambda program, arguments, **options: calls.append(
        (program, arguments)) or 0, cases=K_CASES)
    assert code == 1
    assert calls == [("core_tests", ["--gtest_filter=Small_A.Slow",
                                     f"--gtest_output=xml:{K_TREE / 'test_results' / 'slow' / 'core_tests.small_shard_1of1.xml'}"])]
    gate = reader.commands[1]
    assert gate[gate.index("--rerun") + 1] == str(K_TREE / "test_results" / "slow")
    assert gate[gate.index("--programs") + 1] == str(K_TREE / "Testing" / "programs.json")
    assert console.texts("error") == ["The run broke a time limit."]


def test_a_reader_that_cannot_list_the_run_fails_it_and_judges_nothing_more():
    console = RecordingConsole()
    files = MemoryFiles({K_READER: "", K_JUNIT: "<testsuite/>"})
    reader = _Reader(files, over=(), codes=(2,))
    assert _judge(files, reader, console) == 2
    assert len(reader.commands) == 1
    assert console.texts("error") == [K_UNUSABLE_TEXT]


def test_a_run_without_a_junit_file_is_not_judged():
    console = RecordingConsole()
    files = MemoryFiles({K_READER: ""})
    reader = _Reader(files, over=(), codes=())
    assert _judge(files, reader, console) == 0
    assert reader.commands == []
    assert console.texts("warn") == ["The run wrote no JUnit file, so the budget line is skipped."]


def test_the_failed_tests_rerun_alone_join_the_gate_as_times_alone():
    console = RecordingConsole()
    files = MemoryFiles({K_READER: "", K_JUNIT: "<testsuite/>"})
    reader = _Reader(files, over=(), codes=(0, 0))
    _judge(files, reader, console, rerun=K_TREE / "rerun")
    assert reader.commands[1][reader.commands[1].index("--rerun") + 1] == str(K_TREE / "rerun")
