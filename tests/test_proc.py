"""Spawning, and the two things four copies of it disagreed about."""

import subprocess
from pathlib import Path

from sushicore.proc import Runner


class _Recorder:
    """Stands in for a CLI console module, capturing what was printed."""

    def __init__(self):
        self.lines = []
        self.console = self

    def command(self, text):
        self.lines.append(("command", text))

    def error(self, text):
        self.lines.append(("error", text))

    def print(self, text, **kwargs):
        self.lines.append(("print", text, kwargs))


def test_resolve_exe_falls_back_to_the_name(tmp_path):
    runner = Runner(_Recorder(), "sb")
    assert runner.resolve_exe("definitely-not-on-path") == "definitely-not-on-path"


def test_resolve_exe_reads_path_case_insensitively(tmp_path):
    exe = tmp_path / ("tool.exe" if __import__("os").name == "nt" else "tool")
    exe.write_text("")
    exe.chmod(0o755)
    runner = Runner(_Recorder(), "sb")
    # Case-insensitive compare, not just for the "Path"/"PATH" key this test is
    # named for: shutil.which on Windows appends the extension exactly as
    # PATHEXT spells it ('.EXE' by default), regardless of the on-disk file's
    # own casing ('tool.exe'), so an exact string compare fails here even
    # though resolution found the right file.
    assert runner.resolve_exe("tool", {"Path": str(tmp_path)}).lower() == str(exe).lower()


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
        runner = Runner(_Recorder(), "sb")
        resolved = runner.resolve_exe("tool", {"Path": first, "PATH": second})
        assert resolved.lower() == str(exe).lower()


def test_not_found_message_names_the_program():
    console = _Recorder()
    runner = Runner(console, "sb")
    rc = runner.run(["no-such-binary-anywhere"], cwd=Path("."))
    assert rc == 1
    errors = [t for kind, t, *_ in console.lines if kind == "error"]
    assert errors and "sb config" in errors[0]


def test_drained_output_is_not_parsed_as_markup(monkeypatch):
    """The defect: Rich ate '[[nodiscard]]' out of ctest output in three CLIs."""
    console = _Recorder()

    class _Proc:
        stdout = iter(["note: see [[nodiscard]] here\n"])

        def wait(self):
            return 0

    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: _Proc())
    runner = Runner(console, "sb")
    assert runner.run_drained(["ctest"], cwd=Path(".")) == 0
    prints = [(t, kw) for kind, t, kw in
              (l for l in console.lines if l[0] == "print")]
    assert prints[0][0] == "note: see [[nodiscard]] here"
    assert prints[0][1]["markup"] is False


class _WarnRecorder(_Recorder):
    """A recorder whose console also carries warn()."""

    def warn(self, text):
        self.lines.append(("warn", text))


def _raise(exc):
    def _fn(*a, **k):
        raise exc
    return _fn


def test_missing_exit_code_defaults_to_one_and_is_configurable():
    assert Runner(_Recorder(), "sb").run(["no-such-binary-anywhere"], Path(".")) == 1
    runner = Runner(_Recorder(), "st", missing_exit_code=127)
    assert runner.run(["no-such-binary-anywhere"], Path(".")) == 127


def test_run_drained_returns_the_missing_exit_code(monkeypatch):
    monkeypatch.setattr(subprocess, "Popen", _raise(FileNotFoundError()))
    runner = Runner(_Recorder(), "st", missing_exit_code=127)
    assert runner.run_drained(["ctest"], Path(".")) == 127


def test_interrupt_propagates_by_default(monkeypatch):
    import pytest
    monkeypatch.setattr(subprocess, "run", _raise(KeyboardInterrupt()))
    with pytest.raises(KeyboardInterrupt):
        Runner(_Recorder(), "sb").run(["x"], Path("."))


def test_run_catches_interrupt_when_asked(monkeypatch):
    console = _WarnRecorder()
    monkeypatch.setattr(subprocess, "run", _raise(KeyboardInterrupt()))
    assert Runner(console, "st", catch_interrupt=True).run(["x"], Path(".")) == 130
    assert ("warn", "Interrupted.") in console.lines


def test_run_drained_terminates_the_child_on_interrupt(monkeypatch):
    console = _WarnRecorder()

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
    assert ("warn", "Interrupted.") in console.lines


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
    Runner(_Recorder(), "sb").run_drained(["ctest"], Path("."))
    assert seen["errors"] == "replace"


def test_capture_returns_code_stdout_and_stderr_without_echo():
    import sys
    console = _Recorder()
    script = "import sys; print('o'); print('e', file=sys.stderr); sys.exit(3)"
    code, out, err = Runner(console, "st").capture([sys.executable, "-c", script])
    assert (code, out.strip(), err.strip()) == (3, "o", "e")
    assert console.lines == []


def test_capture_reports_a_missing_executable_quietly():
    console = _Recorder()
    result = Runner(console, "st", missing_exit_code=127).capture(["no-such-binary-anywhere"])
    assert result == (127, "", "Executable not found: 'no-such-binary-anywhere'")
    assert console.lines == []


def test_capture_catches_interrupt(monkeypatch):
    console = _WarnRecorder()
    monkeypatch.setattr(subprocess, "run", _raise(KeyboardInterrupt()))
    assert Runner(console, "st", catch_interrupt=True).capture(["x"]) == (130, "", "")
    assert ("warn", "Interrupted.") in console.lines


def test_capture_returns_the_default_missing_exit_code():
    assert Runner(_Recorder(), "sb").capture(["no-such-binary-anywhere"])[0] == 1


def test_capture_propagates_interrupt_by_default(monkeypatch):
    import pytest
    monkeypatch.setattr(subprocess, "run", _raise(KeyboardInterrupt()))
    with pytest.raises(KeyboardInterrupt):
        Runner(_Recorder(), "sb").capture(["x"])
