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
