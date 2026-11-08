# test_module_plan.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for what a module needs: its package managers, its fragment and its messages."""

from pathlib import Path

import pytest

from sushicore.profile import ModuleProfile
from sushicore.provision import module_plan
from sushicore.provision.config import ProvisionSettings
from sushicore.provision.module_provision import ModuleProvision


def _module(**overrides):
    """Return a module whose fragment is named by *overrides*, or by its manifest."""
    profile = ModuleProfile(name="sushidsp", program="sd", env_prefix="SD", root_marker="m")
    return ModuleProvision(profile=profile, project_root=lambda: Path("."), load_config=lambda: None,
                           console=lambda: None, **overrides)


@pytest.mark.small
def test_windows_uses_winget_a_direct_download_and_vcpkg():
    """Check that Windows provisions through winget, a direct download and vcpkg, in that order."""
    names = [manager.name for manager in
             module_plan.managers_for(ProvisionSettings(platform="windows"))]
    assert names == ["winget", "direct-download", "vcpkg"]


@pytest.mark.small
def test_linux_uses_every_system_manager_and_vcpkg_last():
    """Check that Linux tries every system manager and vcpkg last."""
    names = [manager.name for manager in
             module_plan.managers_for(ProvisionSettings(platform="linux"))]
    assert names == ["apt", "dnf", "yum", "pacman", "zypper", "vcpkg"]


@pytest.mark.small
def test_the_missing_module_message_names_the_module_and_the_variable():
    """Check that the message names the module, the wanter and the variable."""
    message = module_plan.missing_module_message("sushilog", "sushiai")
    assert "sushiai builds on sushilog" in message
    assert "SUSHILOG_DIR" in message


@pytest.mark.small
def test_a_module_that_names_a_fragment_keeps_it_over_the_manifest():
    """Check that a fragment the module names wins over the manifest's."""
    found = module_plan.fragment_of(_module(fragment="from/code.toml"), Path("."),
                                    declared=lambda root: "from/manifest.toml")
    assert found == "from/code.toml"


@pytest.mark.small
def test_a_module_that_names_no_fragment_takes_the_manifest_one():
    """Check that the manifest's fragment is used when the module names none."""
    found = module_plan.fragment_of(_module(), Path("."),
                                    declared=lambda root: "from/manifest.toml")
    assert found == "from/manifest.toml"
