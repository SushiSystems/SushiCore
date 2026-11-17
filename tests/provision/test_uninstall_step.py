# test_uninstall_step.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""What the uninstall step refuses to remove."""

from __future__ import annotations

import pytest

from sushicore.console_memory import RecordingConsole
from sushicore.provision.config import ProvisionSettings
from sushicore.provision.fragments_memory import InMemoryDependencySource
from sushicore.provision.install_context import InstallContext
from sushicore.provision.step_result import StepResult
from sushicore.provision.sinks_memory import InMemoryConfigSink
from sushicore.provision.uninstall_step import UninstallStep


def _context(**overrides) -> InstallContext:
    """Build an install context for a Linux run with *overrides* applied."""
    return InstallContext(cfg=ProvisionSettings(platform="linux"), **overrides)


@pytest.mark.medium
def test_uninstall_leaves_a_refused_root_intact(tmp_path, monkeypatch):
    """Check that a root which is the working directory is refused and left untouched."""
    monkeypatch.chdir(tmp_path)
    sentinel = tmp_path / "marker.txt"
    sentinel.write_text("keep me", encoding="utf-8")
    out = RecordingConsole()
    step = UninstallStep(InMemoryDependencySource([]), managers=[],
                               sink=InMemoryConfigSink(), console=out, root=lambda: tmp_path)

    result = step.run(_context(everything=True))

    assert result is StepResult.FAILED
    assert sentinel.is_file()
    assert any(str(tmp_path) in text for text in out.texts("error"))


@pytest.mark.medium
def test_windows_uninstall_refuses_before_touching_tools(tmp_path):
    """Check that a refused root stops the Windows uninstall before any tool or config is removed."""
    root = tmp_path / "checkout"
    (root / ".git").mkdir(parents=True)
    cmake = root / "tools" / "cmake"
    doxygen = root / "tools" / "doxygen"
    cmake.mkdir(parents=True)
    doxygen.mkdir(parents=True)
    (root / "tools" / "ninja.exe").write_text("", encoding="utf-8")
    sink = InMemoryConfigSink()
    step = UninstallStep(InMemoryDependencySource([]), managers=[], sink=sink,
                               console=RecordingConsole(), root=lambda: root)

    result = step.run(InstallContext(cfg=ProvisionSettings(platform="windows")))

    assert result is StepResult.FAILED
    assert cmake.is_dir() and doxygen.is_dir() and (root / "tools" / "ninja.exe").is_file()
    assert sink.calls == []


@pytest.mark.medium
def test_linux_uninstall_refuses_before_removing_anything(tmp_path):
    """Check that a refused root stops the Linux uninstall before the config is cleared."""
    root = tmp_path / "checkout"
    (root / ".git").mkdir(parents=True)
    sink = InMemoryConfigSink()
    step = UninstallStep(InMemoryDependencySource([]), managers=[], sink=sink,
                               console=RecordingConsole(), root=lambda: root)

    result = step.run(_context())

    assert result is StepResult.FAILED
    assert sink.calls == []
