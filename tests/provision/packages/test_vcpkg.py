# test_vcpkg.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the vcpkg package manager's view of what is installed."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from sushicore.provision.config import ProvisionSettings
from sushicore.provision.packages import vcpkg as vcpkg_mod
from sushicore.provision.packages.vcpkg import VcpkgManager


#: One line of `vcpkg list --triplet x64-windows` output for an installed imgui.
LISTED = "imgui:x64-windows                        1.92.8    Dear ImGui\n"


@pytest.fixture
def manager(tmp_path, monkeypatch):
    """Return a Windows VcpkgManager with a vcpkg file under a folder of its own, listing imgui alone."""
    (tmp_path / "vcpkg.exe").write_text("")
    monkeypatch.setattr(
        vcpkg_mod.subprocess, "run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout=LISTED))
    return VcpkgManager(ProvisionSettings(platform="windows", vcpkg_root=str(tmp_path)))


@pytest.mark.medium
@pytest.mark.parametrize(("package", "installed"), [
    ("imgui[glfw-binding,opengl3-binding]", True),
    ("imgui", True),
    ("glfw3[wayland]", False),
], ids=["a port with features", "a bare port name", "a port that is not listed"])
def test_a_port_is_installed_when_the_listing_holds_its_name(manager, package, installed):
    """Check that a port reads as installed by its name, with or without features."""
    assert manager.is_installed(package) is installed
