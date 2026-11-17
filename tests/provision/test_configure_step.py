# test_configure_step.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""What the configure step writes to its sink."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.console_memory import RecordingConsole
from sushicore.provision.config import ProvisionSettings
from sushicore.provision.configure_step import ConfigureStep
from sushicore.provision.install_context import InstallContext
from sushicore.provision.step_result import StepResult
from sushicore.provision.sinks_memory import InMemoryConfigSink
from sushicore.provision.machine_actions import MachineActions


def _actions(*, paths=None, **overrides) -> MachineActions:
    """Build machine calls that touch nothing and probe *paths*, with *overrides* applied."""
    return MachineActions(**{
        "refresh_path": lambda: None,
        "resolve_config": lambda cfg, gpu=False: dict(paths or {}),
        **overrides})


def _context(**overrides) -> InstallContext:
    """Build an install context for a Linux run with *overrides* applied."""
    return InstallContext(cfg=ProvisionSettings(platform="linux"), **overrides)


@pytest.mark.small
def test_configure_writes_through_the_sink():
    """Check that ConfigureStep hands the probed paths and the active toolchain to its sink."""
    sink = InMemoryConfigSink()
    step = ConfigureStep(sink, console=RecordingConsole(),
                               actions=_actions(paths={"ninja_exe": "n"}))

    result = step.run(_context(active_toolchain="intel-llvm"))

    assert (result, sink.paths, sink.tool) == (
        StepResult.OK, [("linux", {"ninja_exe": "n"})], [{"toolchain": "intel-llvm"}])


@pytest.mark.small
def test_configure_backs_up_before_writing():
    """Check that the sink is asked for a backup before it is asked to write."""
    sink = InMemoryConfigSink(backup_path=Path("stub.toml.bak"))
    out = RecordingConsole()

    ConfigureStep(sink, console=out, actions=_actions(paths={"ninja_exe": "n"})).run(_context())

    assert sink.calls == ["backup", "write_paths"]
    assert "Backed up existing config to stub.toml.bak" in out.texts("info")


@pytest.mark.small
def test_configure_skips_the_backup_line_when_there_is_nothing_to_back_up():
    """Check that no backup line is printed when the sink had no file to back up."""
    sink = InMemoryConfigSink(backup_path=None)
    out = RecordingConsole()

    ConfigureStep(sink, console=out, actions=_actions(paths={"ninja_exe": "n"})).run(_context())

    assert not any(text.startswith("Backed up") for text in out.texts("info"))


@pytest.mark.small
def test_configure_dry_run_prints_the_rendered_config():
    """Check that a dry run prints the config it would write and touches the sink not at all."""
    sink = InMemoryConfigSink()
    out = RecordingConsole()
    step = ConfigureStep(sink, console=out, actions=_actions(paths={"ninja_exe": "n"}))

    result = step.run(_context(dry_run=True))

    assert result is StepResult.OK
    assert any('ninja_exe = "n"' in text for text in out.texts("console.print"))
    assert sink.calls == []
