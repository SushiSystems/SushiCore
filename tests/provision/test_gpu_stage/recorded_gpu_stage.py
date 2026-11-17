# recorded_gpu_stage.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""A GPU stage whose two actions record what they were asked for."""

from __future__ import annotations

from sushicore.console_memory import RecordingConsole
from sushicore.provision.install_context import InstallContext
from sushicore.provision.gpu_stage import GpuStage
from sushicore.provision.machine_actions import MachineActions


class RecordedGpuStage:
    """The two GPU actions of a stage, recording what they were asked for."""

    def __init__(self, *, toolkit_present: bool = False) -> None:
        """Start with nothing recorded; *toolkit_present* answers whether CUDA is already installed."""
        self._toolkit_present = toolkit_present
        self.stacks: list[str] = []
        self.adapters: list[InstallContext] = []

    def stage(self) -> GpuStage:
        """Build a stage whose SDK install and adapter build record into this object."""
        return GpuStage(
            console=RecordingConsole(), actions=MachineActions(refresh_path=lambda: None),
            install_stack=lambda cfg, vendor, dry_run: self.stacks.append(vendor) or True,
            provision_adapters=self.adapters.append,
            toolkit_present=lambda ctx: self._toolkit_present)
