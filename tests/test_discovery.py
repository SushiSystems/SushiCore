# test_discovery.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The shared executable walk, match, and `run`-command resolution policy."""

import os
import stat
from pathlib import Path

import pytest

from sushicore.console_memory import RecordingConsole
from sushicore.discovery import ExecutableIndex


pytestmark = pytest.mark.medium


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
    console = RecordingConsole()
    index = ExecutableIndex()

    exe = index.resolve(tmp_path, console, target="widget")

    assert exe == tmp_path / "widget.exe"
    assert console.texts("error") == []


def test_resolve_reports_a_missing_explicit_target_by_name(tmp_path):
    _exe(tmp_path, "widget")
    console = RecordingConsole()
    index = ExecutableIndex()

    exe = index.resolve(tmp_path, console, target="gadget")

    assert exe is None
    assert console.texts("error") == ["Executable matching 'gadget' not found."]


def test_resolve_falls_back_to_the_default_when_no_target_is_given(tmp_path):
    _exe(tmp_path, "widget")
    console = RecordingConsole()
    index = ExecutableIndex()

    exe = index.resolve(tmp_path, console, default="widget")

    assert exe == tmp_path / "widget.exe"
    assert console.texts("error") == []


def test_resolve_reports_a_missing_default_by_name(tmp_path):
    console = RecordingConsole()
    index = ExecutableIndex()

    exe = index.resolve(tmp_path, console, default="widget")

    assert exe is None
    assert console.texts("error") == ["Default target 'widget' not found."]


def test_resolve_with_sort_ignores_target_and_default_and_delegates_to_select(tmp_path):
    """sort=True must win over an explicit target and a configured default alike.

    The build tree is left empty on purpose: `select` is the only path that
    reports "No executables found" (`match` reports the target/default message
    instead), so seeing that exact message -- rather than either of the other
    two -- is proof the sort branch actually ran first. If the branch order
    were inverted, this would report the target or default message instead and
    the assertion below would fail.
    """
    console = RecordingConsole()
    index = ExecutableIndex()

    exe = index.resolve(tmp_path, console, target="widget", sort=True, default="widget")

    assert exe is None
    assert console.texts("error") == ["No executables found. Build the project first."]


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
    console = RecordingConsole()
    index = ExecutableIndex()

    import rich.prompt
    # find() sorts by lowercased name, so "widget.exe" < "zzz_other.exe": index 2.
    monkeypatch.setattr(rich.prompt.IntPrompt, "ask", staticmethod(lambda *a, **k: 2))

    exe = index.resolve(tmp_path, console, target="widget", sort=True, default="widget")

    assert exe == tmp_path / "zzz_other.exe"
    assert console.texts("error") == []


def _tree(build_root: Path, relative_paths: list[str]) -> None:
    """Create an executable at each of *relative_paths* under *build_root*."""
    for relative in relative_paths:
        folder = build_root / Path(relative).parent
        folder.mkdir(parents=True, exist_ok=True)
        _exe(folder, Path(relative).name)


def _names(found: list[Path]) -> list[str]:
    """Return the file names of *found*, in order."""
    return [path.name for path in found]


def test_find_prunes_the_build_system_folders_and_the_skip_names_at_any_depth(tmp_path):
    _tree(tmp_path, [
        "keep.exe",
        "CMakeFiles/pruned_a.exe",
        "x/_deps/pruned_b.exe",
        "x/y/vcpkg_installed/pruned_c.exe",
        "sibling/pruned_d.exe",
        "x/sibling/pruned_e.exe",
        "x/nested.exe",
    ])
    found = ExecutableIndex(skip_dirs=("sibling",)).find(tmp_path)
    assert _names(found) == ["keep.exe", "nested.exe"]


def test_find_stops_descending_at_max_depth(tmp_path):
    _tree(tmp_path, ["top.exe", "a/mid.exe", "a/b/deep.exe"])
    found = ExecutableIndex(max_depth=1).find(tmp_path)
    assert _names(found) == ["mid.exe", "top.exe"]
