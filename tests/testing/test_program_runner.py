# test_program_runner.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests running a test program of a build tree by the name its shards carry."""

from pathlib import Path

import pytest

from sushicore.console_memory import RecordingConsole
from sushicore.files_memory import MemoryFiles
from sushicore.proc import K_TIMEOUT_EXIT_CODE
from sushicore.proc_memory import RecordingRunner
from sushicore.testing.program_runner import ProgramRunner

pytestmark = pytest.mark.small

K_TREE = Path("/repo/build")
K_FILES = {K_TREE / "CTestTestfile.cmake":
           'add_test([=[core.small_shard_0of2]=] "/repo/build/core" "--gtest_filter=Small_*")\n'}


def _runner(calls, code=0, env=None):
    def run(command, cwd, environment):
        calls.append((command, cwd, environment))
        return code
    return ProgramRunner(K_TREE, run, env, MemoryFiles(K_FILES))


def test_a_program_runs_its_registered_executable_with_the_arguments_in_the_tree_under_the_environment():
    calls = []
    assert _runner(calls, code=3, env={"A": "1"})("core", ["--gtest_filter=Small_A.One"]) == 3
    assert calls == [([str(Path("/repo/build/core")), "--gtest_filter=Small_A.One"], K_TREE, {"A": "1"})]


def test_a_program_the_tree_does_not_register_fails_without_running_anything():
    calls = []
    assert _runner(calls)("missing", []) == 1
    assert calls == []


def test_a_run_given_variables_adds_them_to_the_environment_and_a_timeout_goes_through_the_timed_runner():
    timed = []
    runner = ProgramRunner(K_TREE, lambda *args: 9, {"A": "1"}, MemoryFiles(K_FILES),
                           run_timed=lambda *args: timed.append(args) or 5)
    assert runner("core", ["-x"], env={"B": "2"}, timeout=30.0) == 5
    assert timed == [([str(Path("/repo/build/core")), "-x"], K_TREE, {"A": "1", "B": "2"}, 30.0)]


def test_a_timed_program_runs_through_the_runner_with_its_timeout():
    recording = RecordingRunner(RecordingConsole()).script(7)
    runner = ProgramRunner(K_TREE, lambda *args: 9, None, MemoryFiles(K_FILES), runner=recording)
    assert runner("core", ["-x"], timeout=30.0) == 7
    assert [(c.argv, c.cwd, c.timeout) for c in recording.commands] == [
        ((str(Path("/repo/build/core")), "-x"), K_TREE, 30.0)]


def test_a_timed_program_that_outlives_its_timeout_returns_the_timeout_exit_code():
    recording = RecordingRunner(RecordingConsole()).script_timeout()
    runner = ProgramRunner(K_TREE, lambda *args: 9, None, MemoryFiles(K_FILES), runner=recording)
    assert runner("core", [], timeout=1.0) == K_TIMEOUT_EXIT_CODE
