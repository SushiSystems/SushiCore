"""The shared executable walk, match, and `run`-command resolution policy."""

import os
import stat
from pathlib import Path
from types import SimpleNamespace

from sushicore.discovery import ExecutableIndex


class _FakeConsole:
    """The slice of a CLI's console module ExecutableIndex needs."""

    def __init__(self) -> None:
        self.console = SimpleNamespace(print=lambda *a, **k: None)
        self.errors: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)


def _exe(build_root: Path, name: str) -> Path:
    """Create a file that `_is_executable` recognizes, regardless of platform."""
    path = build_root / (name if name.endswith(".exe") else f"{name}.exe")
    path.write_text("")
    # On Linux `_is_executable` asks os.access for X_OK; the suffix alone is a Windows rule.
    if os.name != "nt":
        path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return path


def test_resolve_finds_an_explicit_target(tmp_path):
    _exe(tmp_path, "widget")
    console = _FakeConsole()
    index = ExecutableIndex()

    exe = index.resolve(tmp_path, console, target="widget")

    assert exe == tmp_path / "widget.exe"
    assert console.errors == []


def test_resolve_reports_a_missing_explicit_target_by_name(tmp_path):
    _exe(tmp_path, "widget")
    console = _FakeConsole()
    index = ExecutableIndex()

    exe = index.resolve(tmp_path, console, target="gadget")

    assert exe is None
    assert console.errors == ["Executable matching 'gadget' not found."]


def test_resolve_falls_back_to_the_default_when_no_target_is_given(tmp_path):
    _exe(tmp_path, "widget")
    console = _FakeConsole()
    index = ExecutableIndex()

    exe = index.resolve(tmp_path, console, default="widget")

    assert exe == tmp_path / "widget.exe"
    assert console.errors == []


def test_resolve_reports_a_missing_default_by_name(tmp_path):
    console = _FakeConsole()
    index = ExecutableIndex()

    exe = index.resolve(tmp_path, console, default="widget")

    assert exe is None
    assert console.errors == ["Default target 'widget' not found."]


def test_resolve_with_sort_ignores_target_and_default_and_delegates_to_select(tmp_path):
    """sort=True must win over an explicit target and a configured default alike.

    The build tree is left empty on purpose: `select` is the only path that
    reports "No executables found" (`match` reports the target/default message
    instead), so seeing that exact message -- rather than either of the other
    two -- is proof the sort branch actually ran first. If the branch order
    were inverted, this would report the target or default message instead and
    the assertion below would fail.
    """
    console = _FakeConsole()
    index = ExecutableIndex()

    exe = index.resolve(tmp_path, console, target="widget", sort=True, default="widget")

    assert exe is None
    assert console.errors == ["No executables found. Build the project first."]


def test_resolve_with_sort_returns_select_choice_even_though_target_also_matches(tmp_path,
                                                                                  monkeypatch):
    """sort=True must reach `select`'s prompt, not just its empty-tree error path.

    *target* names a real, matchable executable here -- if `resolve` checked
    target before sort, it would return that match directly and IntPrompt.ask
    would never be called. Picking the *other* candidate through the (stubbed)
    prompt is proof the sort branch, not the target branch, produced the result.
    """
    _exe(tmp_path, "widget")
    _exe(tmp_path, "zzz_other")
    console = _FakeConsole()
    index = ExecutableIndex()

    import rich.prompt
    # find() sorts by lowercased name, so "widget.exe" < "zzz_other.exe": index 2.
    monkeypatch.setattr(rich.prompt.IntPrompt, "ask", staticmethod(lambda *a, **k: 2))

    exe = index.resolve(tmp_path, console, target="widget", sort=True, default="widget")

    assert exe == tmp_path / "zzz_other.exe"
    assert console.errors == []
