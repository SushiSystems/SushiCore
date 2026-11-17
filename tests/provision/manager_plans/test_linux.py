# test_linux.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The package managers the Linux plan builds."""

from __future__ import annotations

import pytest

from sushicore.provision.config import ProvisionSettings
from sushicore.provision.manager_plans.linux import LinuxManagerPlan
from sushicore.provision.output_memory import MemoryConsole


@pytest.mark.small
def test_linux_provisions_through_every_distro_manager_and_vcpkg_last():
    """Check the managers and their order."""
    managers = LinuxManagerPlan().managers(
        ProvisionSettings(platform="linux"), None, MemoryConsole())

    assert [manager.name for manager in managers] == ["apt", "dnf", "yum", "pacman", "zypper", "vcpkg"]
