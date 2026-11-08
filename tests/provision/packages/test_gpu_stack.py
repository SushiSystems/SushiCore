# test_gpu_stack.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the dispatch of a GPU stack install through the backend registry."""

from __future__ import annotations

import pytest

from sushicore.provision import packages
from sushicore.provision.config import ProvisionSettings
from sushicore.provision.gpu.backend import GpuBackendSpec
from sushicore.provision.gpu.backend_memory import InMemoryToolkitLocator
from sushicore.provision.gpu.registry import Registry


def _spec(locator) -> GpuBackendSpec:
    """Return the spec of a made-up vendor whose locator is *locator*."""
    return GpuBackendSpec(
        vendor="fake",
        probe_vendor="fakevendor",
        locator=locator,
        adapter_option="UR_BUILD_ADAPTER_FAKE",
        adapter_definitions=lambda install: {},
        adapter_target="ur_adapter_fake",
        adapter_binaries=("ur_adapter_fake",),
    )


@pytest.mark.small
def test_install_gpu_stack_dispatches_through_the_registry():
    """Check that the stack of a registered vendor is provisioned by its locator."""
    locator = InMemoryToolkitLocator()
    cfg = ProvisionSettings(platform="linux")

    result = packages.install_gpu_stack(cfg, "fakevendor", dry_run=True,
                                        registry=Registry((_spec(locator),)))

    assert result is True
    assert locator.provisioned_with == [(cfg, True)]


@pytest.mark.small
@pytest.mark.parametrize("vendor", ["none", "unknownvendor"])
def test_install_gpu_stack_reports_no_gpu_for_an_unregistered_vendor(recording_console, vendor):
    """Check that an unregistered vendor gets the CPU-only line and a True answer."""
    cfg = ProvisionSettings(platform="linux")
    assert packages.install_gpu_stack(cfg, vendor, dry_run=True, registry=Registry(())) is True
    assert recording_console.calls == [
        ("info", ("No discrete GPU detected; using the CPU (SPIR/OpenCL) path only.",)),
    ]


@pytest.mark.small
def test_install_gpu_stack_prints_nothing_for_a_registered_vendor(recording_console):
    """Check that a registered vendor gets no CPU-only line."""
    registry = Registry((_spec(InMemoryToolkitLocator()),))
    packages.install_gpu_stack(ProvisionSettings(platform="linux"), "fakevendor", True,
                               registry=registry)
    assert recording_console.calls == []
