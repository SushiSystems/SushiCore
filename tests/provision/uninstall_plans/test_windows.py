# test_windows.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""What the Windows uninstall plan removes."""

from __future__ import annotations

import pytest

from sushicore.console_memory import RecordingConsole
from sushicore.provision.config import ProvisionSettings
from sushicore.provision.fragments import Dependency
from sushicore.provision.fragments_memory import InMemoryDependencySource
from sushicore.provision.packages.base_memory import InMemoryPackageManager
from sushicore.provision.install_context import InstallContext
from sushicore.provision.uninstall_plan import UninstallServices
from sushicore.provision.uninstall_plans.windows import WindowsUninstallPlan


@pytest.mark.medium
def test_the_vcpkg_ports_are_removed_and_a_dry_run_leaves_the_tools(provision_home):
    """Check that ports go to vcpkg and that a dry run says what it would remove, removing nothing."""
    vcpkg = InMemoryPackageManager(name="vcpkg")
    console = RecordingConsole()
    source = InMemoryDependencySource([Dependency(name="hwloc", windows_vcpkg=["hwloc"])])
    services = UninstallServices(source=source, managers=[vcpkg], console=console)
    tools = provision_home / "tools"
    (tools / "cmake").mkdir(parents=True)

    WindowsUninstallPlan().remove_packages(
        InstallContext(cfg=ProvisionSettings(platform="windows"), dry_run=True), services)

    assert vcpkg.removals == [["hwloc"]]
    assert (tools / "cmake").is_dir()
    assert any("would remove" in text for text in console.texts("info"))
