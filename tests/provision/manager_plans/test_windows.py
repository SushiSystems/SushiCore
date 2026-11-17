# test_windows.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The package managers the Windows plan builds."""

from __future__ import annotations

import pytest

from sushicore.provision.config import ProvisionSettings
from sushicore.provision.manager_plans.windows import WindowsManagerPlan
from sushicore.provision.output_memory import MemoryConsole


@pytest.mark.small
def test_windows_provisions_through_winget_a_direct_download_and_vcpkg_in_that_order():
    """Check the managers and their order."""
    managers = WindowsManagerPlan().managers(
        ProvisionSettings(platform="windows"), None, MemoryConsole())

    assert [manager.name for manager in managers] == ["winget", "direct-download", "vcpkg"]


@pytest.mark.small
def test_windows_plan_looks_for_vcpkg_under_its_home(tmp_path, monkeypatch):
    """Check that the vcpkg manager the plan builds finds the tree of the plan's home."""
    from sushicore.provision.dependency_home import DependencyHome

    monkeypatch.setenv("PATH", "")
    tree = tmp_path / "held-root" / "vcpkg"
    tree.mkdir(parents=True)
    (tree / "vcpkg.exe").write_text("")
    held = DependencyHome(lambda: tmp_path / "held-root")
    managers = WindowsManagerPlan(home=held).managers(
        ProvisionSettings(platform="windows"), None, MemoryConsole())

    assert managers[2].name == "vcpkg" and managers[2].available()
