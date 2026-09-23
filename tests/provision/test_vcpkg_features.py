# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""A port asked for with a feature list is the port vcpkg lists without one."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from sushicore.provision.packages import vcpkg as vcpkg_mod
from sushicore.provision.packages.vcpkg import VcpkgManager

#: One line of `vcpkg list --triplet x64-windows` output for an installed imgui.
LISTED = "imgui:x64-windows                        1.92.8    Dear ImGui\n"


@pytest.fixture
def manager(monkeypatch):
    """Return a Windows VcpkgManager whose `vcpkg list` reports imgui alone."""
    monkeypatch.setattr(VcpkgManager, "available", lambda self: True)
    monkeypatch.setattr(
        vcpkg_mod.subprocess, "run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout=LISTED))
    cfg = SimpleNamespace(platform="windows", vcpkg_triplet="", vcpkg_root="",
                           expand=lambda value: value)
    return VcpkgManager(cfg)


def test_a_port_with_features_is_seen_as_installed(manager):
    assert manager.is_installed("imgui[glfw-binding,opengl3-binding]")


def test_a_bare_port_name_still_matches(manager):
    assert manager.is_installed("imgui")


def test_a_port_that_is_not_listed_is_not_installed(manager):
    assert not manager.is_installed("glfw3[wayland]")
