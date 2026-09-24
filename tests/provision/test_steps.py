# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for the seams the shared steps gained."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.provision import home, probe, steps
from sushicore.provision.config import ProvisionSettings
from sushicore.provision.fragments import IDependencySource
from sushicore.provision.pipeline import InstallContext, StepResult


class _EmptySource(IDependencySource):
    """Fake EmptySource for testing."""
    def all(self):
        """Check that all."""
        return []


class _Sink:
    """Fake Sink for testing."""
    def __init__(self, backup_path=None):
        """Perform  init  ."""
        self.target = Path("stub")
        self.paths, self.tool, self.calls = [], [], []
        self._backup_path = backup_path

    def backup(self):
        """Check that backup."""
        self.calls.append("backup")
        return self._backup_path

    def write_paths(self, platform, values):
        """Check that write paths."""
        self.calls.append("write_paths")
        self.paths.append((platform, values))

    def write_tool(self, updates):
        """Check that write tool."""
        self.calls.append("write_tool")
        self.tool.append(updates)

    def clear(self):
        """Check that clear."""
        self.calls.append("clear")


def test_configure_writes_through_the_sink(monkeypatch, recording_console):
    """Check that configure writes through the sink."""
    monkeypatch.setattr(probe, "resolve_local_config", lambda cfg, gpu=False: {"ninja_exe": "n"})
    sink = _Sink()
    ctx = InstallContext(cfg=ProvisionSettings(platform="linux"), active_toolchain="intel-llvm")
    assert steps.ConfigureStep(sink).run(ctx) is StepResult.OK
    assert sink.paths == [("linux", {"ninja_exe": "n"})]
    assert sink.tool == [{"toolchain": "intel-llvm"}]


def test_configure_backs_up_before_writing(monkeypatch, recording_console):
    """Check that configure backs up before writing."""
    monkeypatch.setattr(probe, "resolve_local_config", lambda cfg, gpu=False: {"ninja_exe": "n"})
    sink = _Sink(backup_path=Path("stub.toml.bak"))
    ctx = InstallContext(cfg=ProvisionSettings(platform="linux"))
    steps.ConfigureStep(sink).run(ctx)
    assert sink.calls == ["backup", "write_paths"]
    infos = [args[0] for name, args in recording_console.calls if name == "info"]
    assert any("Backed up existing config to stub.toml.bak" in i for i in infos)


def test_configure_skips_the_backup_line_when_there_is_nothing_to_back_up(
        monkeypatch, recording_console):
    """Check that configure skips the backup line when there is nothing to back up."""
    monkeypatch.setattr(probe, "resolve_local_config", lambda cfg, gpu=False: {"ninja_exe": "n"})
    sink = _Sink(backup_path=None)
    ctx = InstallContext(cfg=ProvisionSettings(platform="linux"))
    steps.ConfigureStep(sink).run(ctx)
    assert sink.calls == ["backup", "write_paths"]
    infos = [args[0] for name, args in recording_console.calls if name == "info"]
    assert not any("Backed up existing config" in i for i in infos)


def test_uninstall_leaves_a_refused_root_intact(tmp_path, monkeypatch, recording_console):
    """Check that uninstall leaves a refused root intact."""
    monkeypatch.chdir(tmp_path)
    home.bind_root(lambda: tmp_path)
    sentinel = tmp_path / "marker.txt"
    sentinel.write_text("keep me", encoding="utf-8")
    try:
        ctx = InstallContext(cfg=ProvisionSettings(platform="linux"), everything=True)
        step = steps.UninstallStep(_EmptySource(), managers=[], sink=_Sink())
        result = step._run_linux(ctx)
    finally:
        home.bind_root(None)

    assert result is StepResult.FAILED
    assert sentinel.is_file()
    errors = [args[0] for name, args in recording_console.calls if name == "error"]
    assert any(str(tmp_path) in e for e in errors)


def test_configure_dry_run_prints_the_rendered_config(monkeypatch, recording_console):
    """Check that configure dry run prints the rendered config."""
    monkeypatch.setattr(probe, "resolve_local_config", lambda cfg, gpu=False: {"ninja_exe": "n"})
    sink = _Sink()
    ctx = InstallContext(cfg=ProvisionSettings(platform="linux"), dry_run=True)
    assert steps.ConfigureStep(sink).run(ctx) is StepResult.OK
    printed = [args[0] for name, args in recording_console.calls if name == "console.print"]
    assert any('ninja_exe = "n"' in text for text in printed)
    assert sink.calls == []


def test_windows_uninstall_refuses_before_touching_tools(tmp_path, recording_console):
    """Check that windows uninstall refuses before touching tools."""
    root = tmp_path / "checkout"
    (root / ".git").mkdir(parents=True)
    cmake = root / "tools" / "cmake"
    doxygen = root / "tools" / "doxygen"
    cmake.mkdir(parents=True)
    doxygen.mkdir(parents=True)
    (root / "tools" / "ninja.exe").write_text("", encoding="utf-8")
    home.bind_root(lambda: root)
    try:
        ctx = InstallContext(cfg=ProvisionSettings(platform="windows"))
        sink = _Sink()
        result = steps.UninstallStep(_EmptySource(), managers=[], sink=sink).run(ctx)
    finally:
        home.bind_root(None)

    assert result is StepResult.FAILED
    assert cmake.is_dir() and doxygen.is_dir() and (root / "tools" / "ninja.exe").is_file()
    assert sink.calls == []


def test_linux_uninstall_refuses_before_removing_anything(tmp_path, recording_console):
    """Check that linux uninstall refuses before removing anything."""
    root = tmp_path / "checkout"
    (root / ".git").mkdir(parents=True)
    home.bind_root(lambda: root)
    try:
        ctx = InstallContext(cfg=ProvisionSettings(platform="linux"))
        sink = _Sink()
        result = steps.UninstallStep(_EmptySource(), managers=[], sink=sink).run(ctx)
    finally:
        home.bind_root(None)

    assert result is StepResult.FAILED
    assert sink.calls == []


@pytest.fixture
def capsys_console(recording_console):
    """Expose the recording console with a ``text`` view of every recorded argument."""
    recording_console.text = lambda: "\n".join(
        str(arg) for _name, args in recording_console.calls for arg in args)
    return recording_console


def _context(**overrides):
    """Build an install context for a Linux run with *overrides* applied."""
    return InstallContext(cfg=ProvisionSettings(platform="linux"), **overrides)


def _run_detect_with_one_missing(ctx):
    """Report an inventory with one missing required dependency through *ctx*."""
    rows = [("ninja", steps._MISSING, "shared", "not found")]
    steps.DetectStep(_EmptySource())._report_inventory(ctx, rows)


def test_missing_dependency_hint_names_the_calling_program(capsys_console):
    """Assert the re-run hint names the program in the context, not hub."""
    ctx = _context(program="st")
    _run_detect_with_one_missing(ctx)
    assert "`st setup`" in capsys_console.text()
    assert "hub install" not in capsys_console.text()


def test_missing_dependency_hint_defaults_to_hub(capsys_console):
    """Assert a context built without a program keeps hub's wording."""
    ctx = _context()
    _run_detect_with_one_missing(ctx)
    assert "`hub install`" in capsys_console.text()
