# test_windows.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""What the Windows install plan installs and reports."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.console_memory import RecordingConsole
from sushicore.provision.config import ProvisionSettings
from sushicore.provision.fragments import Dependency
from sushicore.provision.fragments_memory import InMemoryDependencySource
from sushicore.provision.gpu_stage import GpuStage
from sushicore.provision.install_deps_plan import InstallServices
from sushicore.provision.install_deps_plans.windows import WindowsInstallPlan
from sushicore.provision.machine_actions import MachineActions
from sushicore.provision.packages.base_memory import InMemoryPackageManager
from sushicore.provision.pipeline import InstallContext, StepResult


def _services(managers, dependencies=()) -> InstallServices:
    """Build the services of a run with git and Visual Studio present and no machine touched."""
    console = RecordingConsole()
    actions = MachineActions(refresh_path=lambda: None, install_oneapi=lambda ctx, console: True,
                             which=lambda name: f"/bin/{name}", find_vcvars=lambda: Path("vcvars64.bat"))
    return InstallServices(source=InMemoryDependencySource(list(dependencies)), managers=managers,
                           console=console, actions=actions,
                           gpu=GpuStage(console=console, actions=actions))


def _context(**overrides) -> InstallContext:
    """Build the context of a Windows run with *overrides* applied."""
    return InstallContext(cfg=ProvisionSettings(platform="windows"), **overrides)


@pytest.mark.small
def test_a_run_without_winget_names_no_package_licence():
    """Check that the licences the GPU stage needs come back as they are when winget is absent."""
    assert WindowsInstallPlan().licences(_context(), [], _services([])) == []


@pytest.mark.small
def test_a_run_installs_the_vcpkg_ports_of_a_missing_dependency():
    """Check that the manifest's missing C++ library ports go to vcpkg."""
    vcpkg = InMemoryPackageManager(name="vcpkg")
    dependency = Dependency(name="hwloc", windows_vcpkg=["hwloc"])

    result = WindowsInstallPlan().run(_context(), _services([vcpkg], [dependency]))

    assert result is StepResult.OK
    assert vcpkg.installs == [["hwloc"]]


@pytest.mark.small
def test_a_run_that_needs_ports_but_has_no_vcpkg_fails():
    """Check that a dependency with ports and no vcpkg manager ends the run as failed."""
    dependency = Dependency(name="hwloc", windows_vcpkg=["hwloc"])

    result = WindowsInstallPlan().run(_context(), _services([], [dependency]))

    assert result is StepResult.FAILED
