# test_linux.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The package managers the Linux plan builds."""

from __future__ import annotations

import pytest

from sushicore.provision.config import ProvisionSettings
from sushicore.provision.manager_plans.linux import LinuxManagerPlan
from sushicore.provision.module_plan import managers_for
from sushicore.provision.output_memory import MemoryConsole


@pytest.mark.small
def test_linux_provisions_through_every_distro_manager_and_vcpkg_last():
    """Check the managers and their order."""
    managers = LinuxManagerPlan().managers(
        ProvisionSettings(platform="linux"), None, MemoryConsole())

    assert [manager.name for manager in managers] == ["apt", "dnf", "yum", "pacman", "zypper", "vcpkg"]


@pytest.mark.small
def test_linux_plan_is_built_when_the_run_hands_it_a_download_verifier():
    """Check that a verifier, which Windows uses, does not stop the Linux managers being built."""
    managers = managers_for(ProvisionSettings(platform="linux"), MemoryConsole(), verifier=object())

    assert [manager.name for manager in managers][-1] == "vcpkg"


@pytest.mark.small
def test_linux_plan_looks_for_vcpkg_under_its_home(tmp_path, monkeypatch):
    """Check that the vcpkg manager the plan builds finds the tree of the plan's home."""
    from sushicore.provision.dependency_home import DependencyHome

    monkeypatch.setenv("PATH", "")
    tree = tmp_path / "held-root" / "vcpkg"
    tree.mkdir(parents=True)
    (tree / "vcpkg").write_text("")
    held = DependencyHome(lambda: tmp_path / "held-root")
    managers = LinuxManagerPlan(home=held).managers(
        ProvisionSettings(platform="linux"), None, MemoryConsole())

    assert managers[-1].name == "vcpkg" and managers[-1].available()
