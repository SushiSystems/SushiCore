# test_adapter_provisioner.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests that the GPU stage hands the adapter build everything the provisioner call takes."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.console_memory import RecordingConsole
from sushicore.provision.config import ProvisionSettings
from sushicore.provision.gpu_stage import provision_adapters_for_run
from sushicore.provision.install_context import InstallContext


class _Machine:
    """The machine calls the stage reads, answering a fixed llvm root."""

    def __init__(self) -> None:
        """Hold the three calls."""
        self.refresh_path = lambda: None
        self.resolve_config = lambda cfg, gpu=False, home=None: {"llvm_root": "/opt/llvm"}
        self.detect_vendor = lambda: "none"


class _Provisioner:
    """An adapter provisioner that records the root and whether the run was a dry one."""

    def __init__(self) -> None:
        """Start with no call."""
        self.calls: list[tuple[Path, bool]] = []

    def __call__(self, cfg, registry, toolchain_root, builder, dry_run, *, console) -> None:
        """Record the toolchain root and the dry-run flag."""
        self.calls.append((toolchain_root, dry_run))


@pytest.mark.small
def test_the_provisioner_gets_the_toolchain_root_and_the_dry_run_flag():
    """Check that a dry run reaches the provisioner with the llvm root the machine answered."""
    provisioner = _Provisioner()
    context = InstallContext(cfg=ProvisionSettings(platform="linux"), dry_run=True)
    provision_adapters_for_run(context, console=RecordingConsole(), actions=_Machine(),
                               build_adapters=provisioner)
    assert provisioner.calls == [(Path("/opt/llvm"), True)]
