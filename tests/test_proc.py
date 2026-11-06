# test_proc.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Spawning, and the two things four copies of it disagreed about."""

import json
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


@pytest.mark.medium
def test_resolve_exe_falls_back_to_the_name(tmp_path):
    runner = Runner(RecordingConsole(), "sb")
    assert runner.resolve_exe("definitely-not-on-path") == "definitely-not-on-path"


@pytest.mark.medium
def test_resolve_exe_reads_path_case_insensitively(tmp_path):
    exe = tmp_path / ("tool.exe" if __import__("os").name == "nt" else "tool")
    exe.write_text("")
    exe.chmod(0o755)
    runner = Runner(RecordingConsole(), "sb")
    # shutil.which spells the extension as PATHEXT does; see docs/architecture/OVERVIEW.md, proc.
    assert runner.resolve_exe("tool", {"Path": str(tmp_path)}).lower() == str(exe).lower()


@pytest.mark.medium
def test_resolve_exe_finds_the_tool_when_the_env_holds_both_path_keys():
    """The collision the whole function exists for: os.environ's "Path" plus a
    vcvars overlay's "PATH". Whichever key wins, the tool must still resolve."""
    import os
    import tempfile
    with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
        name = "tool.exe" if os.name == "nt" else "tool"
        exe = Path(second) / name
        exe.write_text("")
        exe.chmod(0o755)
        runner = Runner(RecordingConsole(), "sb")
        resolved = runner.resolve_exe("tool", {"Path": first, "PATH": second})
        assert resolved.lower() == str(exe).lower()


@pytest.mark.medium
def test_not_found_message_names_the_program():
    console = RecordingConsole()
    runner = Runner(console, "sb")
    rc = runner.run(["no-such-binary-anywhere"], cwd=Path("."))
    assert rc == 1
    errors = console.texts("error")
    assert errors and "sb config" in errors[0]


@pytest.mark.medium
def test_drained_output_is_not_parsed_as_markup(monkeypatch):
    """The defect: Rich ate '[[nodiscard]]' out of ctest output in three CLIs."""
    console = RecordingConsole()

    class _Proc:
        stdout = iter(["note: see [[nodiscard]] here\n"])

        def wait(self):
            return 0

    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: _Proc())
    runner = Runner(console, "sb")
    assert runner.run_drained(["ctest"], cwd=Path(".")) == 0
    printed = console.console.printed[0]
    assert printed.text == "note: see [[nodiscard]] here"
    assert printed.options["markup"] is False


def _raise(exc):
    def _fn(*a, **k):
        raise exc
    return _fn


@pytest.mark.medium
def test_missing_exit_code_defaults_to_one_and_is_configurable():
    assert Runner(RecordingConsole(), "sb").run(["no-such-binary-anywhere"], Path(".")) == 1
    runner = Runner(RecordingConsole(), "st", missing_exit_code=127)
    assert runner.run(["no-such-binary-anywhere"], Path(".")) == 127


@pytest.mark.medium
def test_run_drained_returns_the_missing_exit_code(monkeypatch):
    monkeypatch.setattr(subprocess, "Popen", _raise(FileNotFoundError()))
    runner = Runner(RecordingConsole(), "st", missing_exit_code=127)
    assert runner.run_drained(["ctest"], Path(".")) == 127


@pytest.mark.medium
def test_interrupt_propagates_by_default(monkeypatch):
    import pytest
    monkeypatch.setattr(subprocess, "run", _raise(KeyboardInterrupt()))
    with pytest.raises(KeyboardInterrupt):
        Runner(RecordingConsole(), "sb").run(["x"], Path("."))


@pytest.mark.medium
def test_run_catches_interrupt_when_asked(monkeypatch):
    console = RecordingConsole()
    monkeypatch.setattr(subprocess, "run", _raise(KeyboardInterrupt()))
    assert Runner(console, "st", catch_interrupt=True).run(["x"], Path(".")) == 130
    assert console.texts("warn") == ["Interrupted."]


@pytest.mark.medium
def test_run_drained_terminates_the_child_on_interrupt(monkeypatch):
    console = RecordingConsole()

    class _Proc:
        terminated = False
        waited = False

        @property
        def stdout(self):
            raise KeyboardInterrupt

        def terminate(self):
            _Proc.terminated = True

        def wait(self):
            _Proc.waited = _Proc.terminated

    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: _Proc())
    runner = Runner(console, "st", catch_interrupt=True)
    assert runner.run_drained(["ctest"], Path(".")) == 130
    assert _Proc.terminated
    assert _Proc.waited
    assert console.texts("warn") == ["Interrupted."]


@pytest.mark.medium
def test_run_drained_replaces_undecodable_bytes(monkeypatch):
    seen = {}

    class _Proc:
        stdout = iter([])

        def wait(self):
            return 0

    def _popen(*a, **k):
        seen.update(k)
        return _Proc()

    monkeypatch.setattr(subprocess, "Popen", _popen)
    Runner(RecordingConsole(), "sb").run_drained(["ctest"], Path("."))
    assert seen["errors"] == "replace"


@pytest.mark.medium
def test_capture_returns_code_stdout_and_stderr_without_echo():
    import sys
    console = RecordingConsole()
    script = "import sys; print('o'); print('e', file=sys.stderr); sys.exit(3)"
    code, out, err = Runner(console, "st").capture([sys.executable, "-c", script])
    assert (code, out.strip(), err.strip()) == (3, "o", "e")
    assert console.calls == []


@pytest.mark.medium
def test_capture_reports_a_missing_executable_quietly():
    console = RecordingConsole()
    result = Runner(console, "st", missing_exit_code=127).capture(["no-such-binary-anywhere"])
    assert result == (127, "", "Executable not found: 'no-such-binary-anywhere'")
    assert console.calls == []


@pytest.mark.medium
def test_capture_catches_interrupt(monkeypatch):
    console = RecordingConsole()
    monkeypatch.setattr(subprocess, "run", _raise(KeyboardInterrupt()))
    assert Runner(console, "st", catch_interrupt=True).capture(["x"]) == (130, "", "")
    assert console.texts("warn") == ["Interrupted."]


@pytest.mark.medium
def test_capture_returns_the_default_missing_exit_code():
    assert Runner(RecordingConsole(), "sb").capture(["no-such-binary-anywhere"])[0] == 1


@pytest.mark.medium
def test_capture_propagates_interrupt_by_default(monkeypatch):
    import pytest
    monkeypatch.setattr(subprocess, "run", _raise(KeyboardInterrupt()))
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
