# test_level_zero.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests the Level Zero backend spec and its loader locator."""

from __future__ import annotations

import pathlib

from types import SimpleNamespace

import pytest

from sushicore.provision.gpu import level_zero as level_zero_mod

from sushicore.provision.gpu.backend import ToolkitInstall

from sushicore.provision.gpu.level_zero import LEVEL_ZERO



pytestmark = pytest.mark.medium



def test_level_zero_spec_declares_the_adapter_build_inputs():
    """Check that level zero spec declares the adapter build inputs."""
    assert LEVEL_ZERO.vendor == "level_zero"
    assert LEVEL_ZERO.probe_vendor == "intel"
    assert LEVEL_ZERO.adapter_option == "UR_BUILD_ADAPTER_L0"
    assert LEVEL_ZERO.adapter_target == "ur_adapter_level_zero"
    assert LEVEL_ZERO.adapter_binaries == ("ur_adapter_level_zero", "umf")
    install = ToolkitInstall(root=pathlib.Path("/usr"), version=None)
    assert LEVEL_ZERO.adapter_definitions(install) == {}



def test_level_zero_linux_provision_command_matches_the_pinned_text(
        monkeypatch, recording_console):
    """Check that level zero linux provision command matches the pinned text."""
    monkeypatch.setattr(level_zero_mod, "ensure_intel_oneapi_repo", lambda dry_run: True)
    monkeypatch.setattr(level_zero_mod, "is_root", lambda: False)

    cfg = SimpleNamespace(platform="linux")
    assert level_zero_mod.LinuxLevelZeroLocator().provision(cfg, dry_run=True) is True

    commands = [args[0] for name, args in recording_console.calls if name == "command"]
    assert commands == [
        "sudo apt-get update && "
        "sudo apt-get install -y level-zero intel-oneapi-runtime-opencl "
        "intel-oneapi-runtime-libs"
    ]



def test_level_zero_locator_finds_the_loader_via_find_library(monkeypatch):
    """Check that level zero locator finds the loader via find library."""
    monkeypatch.setattr(level_zero_mod.ctypes.util, "find_library",
                         lambda name: "/usr/lib/x86_64-linux-gnu/libze_loader.so.1")
    cfg = SimpleNamespace(platform="linux")

    install = LEVEL_ZERO.locator.locate(cfg)

    assert install == ToolkitInstall(
        root=pathlib.Path("/usr/lib/x86_64-linux-gnu"), version=None,
    )



def test_level_zero_locator_falls_back_to_the_known_lib_dirs(monkeypatch, tmp_path):
    """Check that level zero locator falls back to the known lib dirs."""
    monkeypatch.setattr(level_zero_mod.ctypes.util, "find_library", lambda name: None)
    fake_dir = tmp_path / "lib"
    fake_dir.mkdir()
    (fake_dir / "libze_loader.so.1").write_text("")
    monkeypatch.setattr(level_zero_mod, "_ZE_LOADER_LIB_DIRS", (str(fake_dir),))
    cfg = SimpleNamespace(platform="linux")

    install = LEVEL_ZERO.locator.locate(cfg)

    assert install == ToolkitInstall(root=fake_dir, version=None)



def test_level_zero_locator_reports_nothing_when_the_loader_is_absent(monkeypatch, tmp_path):
    """Check that level zero locator reports nothing when the loader is absent."""
    monkeypatch.setattr(level_zero_mod.ctypes.util, "find_library", lambda name: None)
    monkeypatch.setattr(level_zero_mod, "_ZE_LOADER_LIB_DIRS", (str(tmp_path),))
    cfg = SimpleNamespace(platform="linux")

    assert LEVEL_ZERO.locator.locate(cfg) is None
