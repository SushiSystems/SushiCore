# test_linux.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""What the Linux install plan installs and reports."""

from __future__ import annotations

import pytest

from sushicore.console_memory import RecordingConsole
from sushicore.provision.config import ProvisionSettings
from sushicore.provision.fragments import Dependency
from sushicore.provision.fragments_memory import InMemoryDependencySource
from sushicore.provision.gpu_stage import GpuStage
from sushicore.provision.install_deps_plan import InstallServices
from sushicore.provision.install_deps_plans.linux import K_LINUX_TOOLCHAIN_APT, LinuxInstallPlan
from sushicore.provision.machine_actions import MachineActions
from sushicore.provision.packages.base_memory import InMemoryLinuxPackageManager
from sushicore.provision.pipeline import InstallContext, StepResult


def _services(managers, dependencies=()) -> InstallServices:
    """Build the services of a run that touches no machine and installs through *managers*."""
    console = RecordingConsole()
    actions = MachineActions(refresh_path=lambda: None)
    return InstallServices(source=InMemoryDependencySource(list(dependencies)), managers=managers,
                           console=console, actions=actions,
                           gpu=GpuStage(console=console, actions=actions))


def _context(**overrides) -> InstallContext:
    """Build the context of a Linux run with *overrides* applied."""
    return InstallContext(cfg=ProvisionSettings(platform="linux"), **overrides)


@pytest.mark.small
def test_a_linux_run_names_no_licence_of_its_own():
    """Check that the licences the GPU stage needs come back as they are."""
    needed = []
    assert LinuxInstallPlan().licences(_context(), needed, _services([])) is needed


@pytest.mark.small
@pytest.mark.parametrize(("dry_run", "expected"), [
    (True, StepResult.SKIPPED), (False, StepResult.FAILED),
], ids=["a dry run skips", "a real run fails"])
def test_a_run_without_a_package_manager_stops(dry_run, expected):
    """Check that a machine with no distro manager is skipped on a dry run and failed otherwise."""
    result = LinuxInstallPlan().run(_context(dry_run=dry_run), _services([]))

    assert result is expected


@pytest.mark.small
def test_a_run_installs_the_toolchain_and_the_missing_dependency_through_the_manager():
    """Check that the system toolchain and a dependency's distro packages go to the manager once."""
    manager = InMemoryLinuxPackageManager(name="apt")
    dependency = Dependency(name="hwloc", linux_apt=["libhwloc-dev"])

    result = LinuxInstallPlan().run(_context(), _services([manager], [dependency]))

    assert result is StepResult.OK
    assert manager.installs[0] == [*K_LINUX_TOOLCHAIN_APT, "libhwloc-dev"]
