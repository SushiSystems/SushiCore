# test_linux.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""What the Linux uninstall plan removes."""

from __future__ import annotations

import pytest

from sushicore.console_memory import RecordingConsole
from sushicore.provision.config import ProvisionSettings
from sushicore.provision.fragments import Dependency
from sushicore.provision.fragments_memory import InMemoryDependencySource
from sushicore.provision.packages.base_memory import InMemoryLinuxPackageManager, InMemoryPackageManager
from sushicore.provision.install_context import InstallContext
from sushicore.provision.uninstall_plan import UninstallServices
from sushicore.provision.uninstall_plans.linux import LinuxUninstallPlan


@pytest.mark.small
def test_the_distro_packages_and_the_vcpkg_fallback_ports_are_removed():
    """Check that a dependency's distro packages go to the distro manager and its ports to vcpkg."""
    apt = InMemoryLinuxPackageManager(name="apt")
    vcpkg = InMemoryPackageManager(name="vcpkg")
    source = InMemoryDependencySource([
        Dependency(name="hwloc", linux_apt=["libhwloc-dev"]),
        Dependency(name="fmt", windows_vcpkg=["fmt"]),
    ])
    services = UninstallServices(source=source, managers=[apt, vcpkg], console=RecordingConsole())

    LinuxUninstallPlan().remove_packages(
        InstallContext(cfg=ProvisionSettings(platform="linux")), services)

    assert (apt.removals, vcpkg.removals) == ([["libhwloc-dev"]], [["fmt"]])
