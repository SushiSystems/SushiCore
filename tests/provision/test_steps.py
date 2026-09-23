# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for the seams the shared steps gained."""

from __future__ import annotations

from pathlib import Path

from sushicore.provision import home, probe, steps
from sushicore.provision.config import ProvisionSettings
from sushicore.provision.fragments import IDependencySource
from sushicore.provision.pipeline import InstallContext, StepResult


class _EmptySource(IDependencySource):
    def all(self):
        return []


class _Sink:
    def __init__(self, backup_path=None):
        self.target = Path("stub")
        self.paths, self.tool, self.calls = [], [], []
        self._backup_path = backup_path

    def backup(self):
        self.calls.append("backup")
        return self._backup_path

    def write_paths(self, platform, values):
        self.calls.append("write_paths")
        self.paths.append((platform, values))

    def write_tool(self, updates):
        self.calls.append("write_tool")
        self.tool.append(updates)


def test_configure_writes_through_the_sink(monkeypatch, recording_console):
    monkeypatch.setattr(probe, "resolve_local_config", lambda cfg, gpu=False: {"ninja_exe": "n"})
    sink = _Sink()
    ctx = InstallContext(cfg=ProvisionSettings(platform="linux"), active_toolchain="intel-llvm")
    assert steps.ConfigureStep(sink).run(ctx) is StepResult.OK
    assert sink.paths == [("linux", {"ninja_exe": "n"})]
    assert sink.tool == [{"toolchain": "intel-llvm"}]


def test_configure_backs_up_before_writing(monkeypatch, recording_console):
    monkeypatch.setattr(probe, "resolve_local_config", lambda cfg, gpu=False: {"ninja_exe": "n"})
    sink = _Sink(backup_path=Path("stub.toml.bak"))
    ctx = InstallContext(cfg=ProvisionSettings(platform="linux"))
    steps.ConfigureStep(sink).run(ctx)
    assert sink.calls == ["backup", "write_paths"]
    infos = [args[0] for name, args in recording_console.calls if name == "info"]
    assert any("Backed up existing config to stub.toml.bak" in i for i in infos)


def test_configure_skips_the_backup_line_when_there_is_nothing_to_back_up(
        monkeypatch, recording_console):
    monkeypatch.setattr(probe, "resolve_local_config", lambda cfg, gpu=False: {"ninja_exe": "n"})
    sink = _Sink(backup_path=None)
    ctx = InstallContext(cfg=ProvisionSettings(platform="linux"))
    steps.ConfigureStep(sink).run(ctx)
    assert sink.calls == ["backup", "write_paths"]
    infos = [args[0] for name, args in recording_console.calls if name == "info"]
    assert not any("Backed up existing config" in i for i in infos)


def test_uninstall_leaves_a_refused_root_intact(tmp_path, monkeypatch, recording_console):
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
