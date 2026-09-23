# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""``install_gpu_stack`` dispatches through the registry and reports no GPU cleanly."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from sushicore.provision import packages
from sushicore.provision import probe
from sushicore.provision.gpu.registry import Registry


class _RecordingLocator:
    """A locator that records whether it was asked to provision."""

    def __init__(self) -> None:
        """Start with no recorded call."""
        self.provisioned_with: tuple | None = None

    def locate(self, cfg):
        """Report no toolkit; this fake never needs to be found."""
        return None

    def provision(self, cfg, dry_run: bool) -> bool:
        """Record the call and report success."""
        self.provisioned_with = (cfg, dry_run)
        return True


def test_install_gpu_stack_dispatches_through_the_registry(monkeypatch):
    """Check that install gpu stack dispatches through the registry."""
    from sushicore.provision.gpu.backend import GpuBackendSpec

    locator = _RecordingLocator()
    fake_spec = GpuBackendSpec(
        vendor="fake",
        probe_vendor="fakevendor",
        locator=locator,
        adapter_option="UR_BUILD_ADAPTER_FAKE",
        adapter_definitions=lambda install: {},
        adapter_target="ur_adapter_fake",
        adapter_binaries=("ur_adapter_fake",),
    )
    fake_registry = Registry((fake_spec,))
    monkeypatch.setattr(packages.gpu_stack, "DEFAULT_REGISTRY", fake_registry)

    cfg = SimpleNamespace(platform="linux")
    result = packages.install_gpu_stack(cfg, "fakevendor", dry_run=True)

    assert result is True
    assert locator.provisioned_with == (cfg, True)


def test_install_gpu_stack_reports_no_gpu_for_an_unregistered_vendor(
        monkeypatch, recording_console):
    """Check that install gpu stack reports no gpu for an unregistered vendor."""
    fake_registry = Registry(())
    monkeypatch.setattr(packages.gpu_stack, "DEFAULT_REGISTRY", fake_registry)

    cfg = SimpleNamespace(platform="linux")
    assert packages.install_gpu_stack(cfg, "none", dry_run=True) is True
    assert recording_console.calls == [
        ("info", ("No discrete GPU detected; using the CPU (SPIR/OpenCL) path only.",)),
    ]


@pytest.mark.parametrize("adapters, printed", [
    ("intel(r) uhd graphics 630", False),
    ("microsoft basic display adapter", True),
])
def test_no_discrete_gpu_prints_only_without_a_known_vendor(
        monkeypatch, recording_console, adapters, printed):
    """Check that no discrete gpu prints only without a known vendor."""
    monkeypatch.setattr(probe.shutil, "which", lambda name: None)
    monkeypatch.setattr(probe.sys, "platform", "win32")
    monkeypatch.setattr(probe, "_windows_display_adapters", lambda: adapters)

    cfg = SimpleNamespace(platform="windows")
    packages.install_gpu_stack(cfg, probe.detect_gpu_vendor(), dry_run=True)

    infos = [args[0] for name, args in recording_console.calls if name == "info"]
    assert any("No discrete GPU detected" in msg for msg in infos) is printed
