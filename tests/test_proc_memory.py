# test_proc_memory.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""What the recording runner promises beyond the runner contract in test_proc.py."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.console_memory import RecordingConsole
from sushicore.proc_memory import RecordedCommand, RecordingRunner

pytestmark = pytest.mark.small


@pytest.fixture
def runner() -> RecordingRunner:
    return RecordingRunner(RecordingConsole())


def test_the_runner_records_each_command_with_its_folder_and_environment(runner):
    runner.run(["cmake", "--build", "."], Path("build"), {"A": "1"})
    assert runner.commands == [
        RecordedCommand(("cmake", "--build", "."), Path("build"), {"A": "1"}, False)]


def test_the_runner_records_a_command_given_no_environment_as_none(runner):
    runner.run(["ninja"], Path("."))
    assert runner.commands[0].env is None


def test_the_runner_records_a_drained_run_as_drained(runner):
    runner.run_drained(["ctest"], Path("."))
    assert runner.commands[0].drained is True


def test_the_runner_records_commands_in_the_order_they_ran(runner):
    runner.run(["first"], Path("."))
    runner.run_drained(["second"], Path("."))
    assert [command.argv[0] for command in runner.commands] == ["first", "second"]


def test_a_recorded_environment_does_not_follow_later_changes_to_the_dictionary(runner):
    env = {"A": "1"}
    runner.run(["tool"], Path("."), env)
    env["A"] = "2"
    assert runner.commands[0].env == {"A": "1"}


def test_the_runner_answers_scripted_results_in_the_order_scripted(runner):
    runner.script(4).script(0)
    assert [runner.run(["a"], Path(".")), runner.run(["b"], Path("."))] == [4, 0]


def test_a_command_with_no_script_left_exits_zero(runner):
    assert runner.run(["unscripted"], Path(".")) == 0


def test_a_plain_run_prints_none_of_the_scripted_lines():
    console = RecordingConsole()
    RecordingRunner(console).script(0, ("out",)).run(["tool"], Path("."))
    assert console.console.printed == []


def test_the_runner_records_a_capture_as_captured(runner):
    runner.capture(["git", "status"], Path("repo"))
    assert runner.commands == [
        RecordedCommand(("git", "status"), Path("repo"), None, drained=False, captured=True)]


def test_a_capture_returns_the_scripted_error_output(runner):
    runner.script(2, stderr="fatal: not a repository")
    assert runner.capture(["git", "status"])[2] == "fatal: not a repository"
