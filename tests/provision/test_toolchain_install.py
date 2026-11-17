# test_toolchain_install.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Which SYCL toolchains a run installs."""

from __future__ import annotations

import pytest

from sushicore.console_memory import RecordingConsole
from sushicore.provision.config import ProvisionSettings
from sushicore.provision.fragments_memory import InMemoryDependencySource
from sushicore.provision.gpu_stage import GpuStage
from sushicore.provision.install_deps_plan import InstallServices
from sushicore.provision.machine_actions import MachineActions
from sushicore.provision.install_context import InstallContext
from sushicore.provision.toolchain_install import install_toolchains


@pytest.mark.small
def test_a_run_that_selects_no_toolchain_installs_and_records_nothing():
    """Check that nothing is installed, recorded or reported when no toolchain is selected."""
    console = RecordingConsole()
    actions = MachineActions(refresh_path=lambda: None)
    services = InstallServices(source=InMemoryDependencySource([]), managers=[], console=console,
                               actions=actions, gpu=GpuStage(console=console, actions=actions))
    ctx = InstallContext(cfg=ProvisionSettings(platform="linux"))

    install_toolchains(ctx, services, mgr=None, vcpkg=None)

    assert (ctx.resolved_paths, console.texts("warn")) == ({}, [])
