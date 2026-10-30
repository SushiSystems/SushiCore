# test_module_plan.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests the choices a module's plan makes: package managers and the message for a missing checkout."""

import pytest

from sushicore.provision import module_plan
from sushicore.provision.config import ProvisionSettings


pytestmark = pytest.mark.small


def test_windows_uses_winget_a_direct_download_and_vcpkg():
    cfg = ProvisionSettings(platform="windows")
    names = [type(manager).__name__ for manager in module_plan.managers_for(cfg)]
    assert names == ["WingetManager", "DirectDownloadWindowsManager", "VcpkgManager"]


def test_linux_uses_every_system_manager_and_vcpkg_last():
    cfg = ProvisionSettings(platform="linux")
    names = [type(manager).__name__ for manager in module_plan.managers_for(cfg)]
    assert names[0] == "AptManager"
    assert names[-1] == "VcpkgManager"
    assert len(names) == 6


def test_the_missing_module_message_names_the_module_and_the_variable():
    message = module_plan.missing_module_message("sushilog", "sushiai")
    assert "sushiai builds on sushilog" in message
    assert "SUSHILOG_DIR" in message


def test_a_module_that_names_a_fragment_keeps_it_over_the_manifest(tmp_path):
    from pathlib import Path

    from sushicore.profile import ModuleProfile
    from sushicore.provision.module_provision import ModuleProvision

    (tmp_path / "sushi-module.toml").write_text('[module]\nfragment = "from/manifest.toml"\n', encoding="utf-8")
    profile = ModuleProfile(name="sushidsp", program="sd", env_prefix="SD", root_marker="m")

    def module(**overrides):
        return ModuleProvision(profile=profile, project_root=lambda: Path("."), load_config=lambda: None,
                               console=lambda: None, **overrides)

    assert module_plan.fragment_of(module(), tmp_path) == "from/manifest.toml"
    assert module_plan.fragment_of(module(fragment="from/code.toml"), tmp_path) == "from/code.toml"
