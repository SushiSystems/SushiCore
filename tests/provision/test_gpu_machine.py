# test_gpu_machine.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests that the GPU stage runs against any object holding the machine calls it reads."""

from __future__ import annotations

import pytest

from sushicore.console_memory import RecordingConsole
from sushicore.provision.config import ProvisionSettings
from sushicore.provision.gpu_stage import provision_adapters_for_run
from sushicore.provision.install_context import InstallContext


class _FixedMachine:
    """A machine that is not MachineActions: it holds the three calls the stage reads."""

    def __init__(self) -> None:
        """Hold the three calls, the path refresh recording that it ran."""
        self.refreshed = False
        self.refresh_path = self._refresh
        self.resolve_config = lambda cfg, gpu=False, home=None: {"llvm_root": "/opt/llvm"}
        self.detect_vendor = lambda: "none"

    def _refresh(self) -> None:
        """Record that PATH was reloaded."""
        self.refreshed = True


@pytest.mark.small
def test_the_adapter_build_runs_against_a_machine_that_is_not_machine_actions():
    """Check that the stage reads the llvm root off any object holding the three calls."""
    machine = _FixedMachine()
    roots = []
    provision_adapters_for_run(
        InstallContext(cfg=ProvisionSettings(platform="linux")), console=RecordingConsole(),
        actions=machine,
        build_adapters=lambda cfg, registry, root, builder, dry_run, console: roots.append(str(root)))
    assert machine.refreshed is True
    assert len(roots) == 1 and roots[0].replace("\\", "/") == "/opt/llvm"
