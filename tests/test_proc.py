# test_proc.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Spawning, and the two things four copies of it disagreed about."""

import json
import os
import shutil
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import pytest

from sushicore.console_memory import RecordingConsole
from sushicore.proc import K_TIMEOUT_EXIT_CODE, CommandRunner, Runner
from sushicore.proc_memory import RecordingRunner

K_LINES = ["note: see [[nodiscard]] here", "second line"]
K_MISSING_EXIT_CODE = 127


class _Child:
    """Stands in for the process `subprocess.Popen` starts: it prints lines and exits."""

    def __init__(self, lines: list[str] | None = None, exit_code: int = 0) -> None:
        self.stdout = iter(lines or [])
        self._exit_code = exit_code

    def wait(self) -> int:
        """Return the exit code the child was given."""
        return self._exit_code


class _InterruptedChild:
    """Stands in for a child whose output is read when the user presses Ctrl+C."""

    def __init__(self) -> None:
        self.terminated = False
        self.waited_after_terminating = False

    @property
    def stdout(self):
        """Raise the interrupt the user's Ctrl+C raises."""
        raise KeyboardInterrupt

    def terminate(self) -> None:
        """Record that the child was told to stop."""
        self.terminated = True

    def wait(self) -> int:
        """Record whether the child had been told to stop before it was waited for."""
        self.waited_after_terminating = self.terminated
        return 0


def _raising(error: BaseException) -> Callable[..., None]:
    """Return a function that raises *error* whatever it is called with."""
    def raise_error(*args, **kwargs):
        raise error
    return raise_error


def _executable(folder: Path) -> Path:
    """Create a program named `tool` in *folder* the way the platform names one, and return it."""
    program = folder / ("tool.exe" if os.name == "nt" else "tool")
    program.write_text("")
    program.chmod(0o755)
    return program


@pytest.fixture
def nothing_on_path(monkeypatch):
    """Make the PATH search find no program, so a test reads neither PATH nor the disk."""
    monkeypatch.setattr(shutil, "which", lambda *args, **kwargs: None)


@pytest.fixture
def child_is_missing(monkeypatch, nothing_on_path):
    """Make every spawn fail as it does for a program that does not exist."""
    monkeypatch.setattr(subprocess, "run", _raising(FileNotFoundError()))
    monkeypatch.setattr(subprocess, "Popen", _raising(FileNotFoundError()))


@pytest.fixture
def user_interrupts(monkeypatch, nothing_on_path):
    """Make a run of a child raise the interrupt that Ctrl+C raises."""
    monkeypatch.setattr(subprocess, "run", _raising(KeyboardInterrupt()))


@pytest.mark.small
def test_resolve_exe_falls_back_to_the_name(nothing_on_path):
    runner = Runner(RecordingConsole(), "sb")
    assert runner.resolve_exe("definitely-not-on-path") == "definitely-not-on-path"


@pytest.mark.medium
def test_resolve_exe_reads_path_case_insensitively(tmp_path):
    exe = _executable(tmp_path)
    runner = Runner(RecordingConsole(), "sb")
    # shutil.which spells the extension as PATHEXT does; see docs/architecture/OVERVIEW.md, proc.
    assert runner.resolve_exe("tool", {"Path": str(tmp_path)}).lower() == str(exe).lower()


@pytest.mark.medium
def test_resolve_exe_finds_the_tool_when_the_env_holds_both_path_keys(tmp_path):
    """The collision the whole function exists for: os.environ's "Path" plus a
    vcvars overlay's "PATH". Whichever key wins, the tool must still resolve."""
    first, second = tmp_path / "first", tmp_path / "second"
    first.mkdir()
    second.mkdir()
    exe = _executable(second)
    runner = Runner(RecordingConsole(), "sb")
    resolved = runner.resolve_exe("tool", {"Path": str(first), "PATH": str(second)})
    assert resolved.lower() == str(exe).lower()


@pytest.mark.small
def test_not_found_message_names_the_program(child_is_missing):
    console = RecordingConsole()
    runner = Runner(console, "sb")
    rc = runner.run(["no-such-binary-anywhere"], cwd=Path("."))
    assert rc == 1
    assert "sb config" in console.texts("error")[0]


@pytest.mark.small
def test_drained_output_is_not_parsed_as_markup(monkeypatch, nothing_on_path):
    """The defect: Rich ate '[[nodiscard]]' out of ctest output in three CLIs."""
    console = RecordingConsole()
    monkeypatch.setattr(subprocess, "Popen", lambda *args, **kwargs: _Child([K_LINES[0] + "\n"]))
    runner = Runner(console, "sb")
    assert runner.run_drained(["ctest"], cwd=Path(".")) == 0
    printed = console.console.printed[0]
    assert printed.text == K_LINES[0]
    assert printed.options["markup"] is False


@pytest.mark.small
@pytest.mark.parametrize("options, expected", [
    ({}, 1),
    ({"missing_exit_code": 127}, 127),
], ids=["default", "configured"])
def test_missing_exit_code_defaults_to_one_and_is_configurable(
        child_is_missing, options, expected):
    runner = Runner(RecordingConsole(), "st", **options)
    assert runner.run(["no-such-binary-anywhere"], Path(".")) == expected


@pytest.mark.small
def test_run_drained_returns_the_missing_exit_code(child_is_missing):
    runner = Runner(RecordingConsole(), "st", missing_exit_code=127)
    assert runner.run_drained(["ctest"], Path(".")) == 127


@pytest.mark.small
def test_interrupt_propagates_by_default(user_interrupts):
    with pytest.raises(KeyboardInterrupt):
        Runner(RecordingConsole(), "sb").run(["x"], Path("."))


@pytest.mark.small
def test_run_catches_interrupt_when_asked(user_interrupts):
    console = RecordingConsole()
    assert Runner(console, "st", catch_interrupt=True).run(["x"], Path(".")) == 130
    assert console.texts("warn") == ["Interrupted."]


@pytest.mark.small
def test_run_drained_terminates_the_child_on_interrupt(monkeypatch, nothing_on_path):
    console = RecordingConsole()
    child = _InterruptedChild()
    monkeypatch.setattr(subprocess, "Popen", lambda *args, **kwargs: child)
    runner = Runner(console, "st", catch_interrupt=True)
    assert runner.run_drained(["ctest"], Path(".")) == 130
    assert (child.terminated, child.waited_after_terminating) == (True, True)
    assert console.texts("warn") == ["Interrupted."]


@pytest.mark.medium
def test_run_drained_replaces_undecodable_bytes():
    console = RecordingConsole()
    # The bytes "ok ", 0x81 and a newline: 0x81 is invalid UTF-8 and undefined in cp1252.
    code = "import sys; sys.stdout.buffer.write(bytes([111, 107, 32, 129, 10]))"
    assert Runner(console, "sb").run_drained([sys.executable, "-c", code], Path(".")) == 0
    assert [out.text for out in console.console.printed] == ["ok �"]


@pytest.mark.small
def test_capture_returns_code_stdout_and_stderr_without_echo(monkeypatch, nothing_on_path):
    console = RecordingConsole()
    finished = subprocess.CompletedProcess(["tool"], 3, stdout="o\n", stderr="e\n")
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: finished)
    code, out, err = Runner(console, "st").capture(["tool"])
    assert (code, out, err) == (3, "o\n", "e\n")
    assert console.calls == []


@pytest.mark.small
def test_capture_reports_a_missing_executable_quietly(child_is_missing):
    console = RecordingConsole()
    result = Runner(console, "st", missing_exit_code=127).capture(["no-such-binary-anywhere"])
    assert result == (127, "", "Executable not found: 'no-such-binary-anywhere'")
    assert console.calls == []


@pytest.mark.small
def test_capture_catches_interrupt(user_interrupts):
    console = RecordingConsole()
    assert Runner(console, "st", catch_interrupt=True).capture(["x"]) == (130, "", "")
    assert console.texts("warn") == ["Interrupted."]


@pytest.mark.small
def test_capture_returns_the_default_missing_exit_code(child_is_missing):
    assert Runner(RecordingConsole(), "sb").capture(["no-such-binary-anywhere"])[0] == 1


@pytest.mark.small
def test_capture_propagates_interrupt_by_default(user_interrupts):
    with pytest.raises(KeyboardInterrupt):
        Runner(RecordingConsole(), "sb").capture(["x"])


@dataclass
class RunnerWorld:
    """A runner under test, its console, and the commands that make it answer in a known way."""

    runner: CommandRunner
    console: RecordingConsole
    exiting: Callable[[int, list[str]], list[str]]
    missing: Callable[[], list[str]]
    hanging: Callable[[], list[str]]


class CommandRunnerContract:
    """The promises every :class:`CommandRunner` keeps; a subclass supplies the world."""

    @pytest.mark.parametrize("method", ["run", "run_drained"])
    @pytest.mark.parametrize("exit_code", [0, 3])
    def test_a_run_returns_the_exit_code_of_the_command(self, world, method, exit_code):
        argv = world.exiting(exit_code, [])
        assert getattr(world.runner, method)(argv, Path(".")) == exit_code

    @pytest.mark.parametrize("method", ["run", "run_drained"])
    def test_a_run_echoes_the_command_line_once(self, world, method):
        argv = world.exiting(0, [])
        getattr(world.runner, method)(argv, Path("."))
        (echoed,) = world.console.texts("command")
        assert argv[-1] in echoed

    def test_a_drained_run_prints_each_output_line_in_order(self, world):
        argv = world.exiting(0, K_LINES)
        world.runner.run_drained(argv, Path("."))
        assert [out.text for out in world.console.console.printed] == K_LINES

    def test_a_drained_run_prints_output_without_parsing_markup(self, world):
        argv = world.exiting(0, K_LINES)
        world.runner.run_drained(argv, Path("."))
        assert [out.options["markup"] for out in world.console.console.printed] == [False, False]

    @pytest.mark.parametrize("method", ["run", "run_drained"])
    def test_a_missing_executable_returns_the_missing_exit_code(self, world, method):
        assert getattr(world.runner, method)(world.missing(), Path(".")) == K_MISSING_EXIT_CODE

    @pytest.mark.parametrize("method", ["run", "run_drained"])
    def test_a_missing_executable_is_reported_as_one_error(self, world, method):
        getattr(world.runner, method)(world.missing(), Path("."))
        assert len(world.console.texts("error")) == 1

    def test_a_program_found_on_no_path_resolves_to_its_own_name(self, world):
        assert world.runner.resolve_exe("no-such-binary-anywhere") == "no-such-binary-anywhere"

    @pytest.mark.parametrize("exit_code", [0, 3])
    def test_a_capture_returns_the_exit_code_and_each_output_line(self, world, exit_code):
        argv = world.exiting(exit_code, K_LINES)
        code, stdout, _ = world.runner.capture(argv, Path("."))
        assert (code, stdout.splitlines()) == (exit_code, K_LINES)

    def test_a_capture_prints_nothing(self, world):
        world.runner.capture(world.exiting(0, K_LINES), Path("."))
        assert (world.console.texts("command"), world.console.console.printed) == ([], [])

    def test_a_capture_of_a_missing_executable_returns_the_missing_exit_code_quietly(self, world):
        code, stdout, stderr = world.runner.capture(world.missing(), Path("."))
        assert (code, stdout, "no-such-binary-anywhere" in stderr, world.console.texts("error")) == (
            K_MISSING_EXIT_CODE, "", True, [])

    def test_a_capture_that_outlives_its_timeout_returns_the_timeout_exit_code(self, world):
        code, _, stderr = world.runner.capture(world.hanging(), Path("."), timeout=0.5)
        assert (code, "timed out" in stderr) == (K_TIMEOUT_EXIT_CODE, True)

    def test_a_capture_within_its_timeout_returns_as_without_one(self, world):
        code, stdout, _ = world.runner.capture(world.exiting(0, K_LINES), Path("."), timeout=30)
        assert (code, stdout.splitlines()) == (0, K_LINES)


@pytest.mark.small
class TestRecordingRunnerKeepsTheRunnerContract(CommandRunnerContract):
    """The in-memory runner, spawning nothing."""

    @pytest.fixture
    def world(self):
        console = RecordingConsole()
        runner = RecordingRunner(console, missing_exit_code=K_MISSING_EXIT_CODE)

        def exiting(exit_code, lines):
            runner.script(exit_code, tuple(lines))
            return ["tool", f"--exit-{exit_code}"]

        def missing():
            runner.script_missing()
            return ["no-such-binary-anywhere"]

        def hanging():
            runner.script_timeout()
            return ["tool", "--hang"]

        return RunnerWorld(runner, console, exiting, missing, hanging)


@pytest.mark.medium
class TestRunnerKeepsTheRunnerContract(CommandRunnerContract):
    """The real runner, spawning the Python that runs the tests."""

    @pytest.fixture
    def world(self):
        console = RecordingConsole()
        runner = Runner(console, "st", missing_exit_code=K_MISSING_EXIT_CODE)

        def exiting(exit_code, lines):
            code = f"import sys; [print(line) for line in {json.dumps(lines)}]; sys.exit({exit_code})"
            return [sys.executable, "-c", code]

        def missing():
            return ["no-such-binary-anywhere"]

        def hanging():
            return [sys.executable, "-c", "import time; time.sleep(30)"]

        return RunnerWorld(runner, console, exiting, missing, hanging)
