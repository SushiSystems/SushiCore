# test_registry.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The GPU backend registry indexes specs by vendor and probe key and rejects duplicates."""

from __future__ import annotations

import pathlib
from types import SimpleNamespace

import pytest

from sushicore.provision.gpu.backend import (
    GpuBackendSpec,
    NotProvided,
    PlatformLocator,
    ToolkitInstall,
)
from sushicore.provision.gpu.backend_memory import InMemoryToolkitLocator
from sushicore.provision.gpu.registry import Registry


pytestmark = pytest.mark.small


def _locator(root: str) -> InMemoryToolkitLocator:
    """Return a locator that reports an install rooted at *root*."""
    return InMemoryToolkitLocator(ToolkitInstall(root=pathlib.Path(root), version="1.0"))


def _fake_spec(vendor: str = "fake", probe_vendor: str = "fakevendor",
               locator=None) -> GpuBackendSpec:
    """Build one GpuBackendSpec whose fields carry no real toolkit behaviour."""
    return GpuBackendSpec(
        vendor=vendor,
        probe_vendor=probe_vendor,
        locator=locator or _locator("/opt/fake"),
        adapter_option="UR_BUILD_ADAPTER_FAKE",
        adapter_definitions=lambda install: {"FAKE_ROOT": str(install.root)},
        adapter_target="ur_adapter_fake",
        adapter_binaries=("ur_adapter_fake",),
    )


def test_a_registered_spec_is_found_by_vendor_and_probe_key():
    """Check that a registered spec is found by vendor and probe key."""
    spec = _fake_spec()
    registry = Registry((spec,))
    assert registry.for_vendor("fake") is spec
    assert registry.for_probe_vendor("fakevendor") is spec
    assert registry.all() == (spec,)


def test_an_unknown_vendor_or_probe_key_returns_none():
    """Check that an unknown vendor or probe key returns none."""
    registry = Registry((_fake_spec(),))
    assert registry.for_vendor("missing") is None
    assert registry.for_probe_vendor("missing") is None


@pytest.mark.parametrize(("first", "second"), [
    (("fake", "a"), ("fake", "b")),
    (("a", "fakevendor"), ("b", "fakevendor")),
], ids=["duplicate-vendor-name", "duplicate-probe-vendor"])
def test_a_duplicate_vendor_or_probe_vendor_is_refused(first, second):
    """Check that two specs sharing a vendor name, or a probe key, are refused."""
    with pytest.raises(ValueError):
        Registry((_fake_spec(*first), _fake_spec(*second)))


def test_platform_locator_dispatches_to_the_matching_platform():
    """Check that platform locator dispatches to the matching platform."""
    linux_locator = _locator("/opt/fake-linux")
    dispatcher = PlatformLocator("fake", {"linux": linux_locator})
    cfg = SimpleNamespace(platform="linux")

    install = dispatcher.locate(cfg)
    assert install == ToolkitInstall(root=pathlib.Path("/opt/fake-linux"), version="1.0")

    assert dispatcher.provision(cfg, dry_run=False) is True
    assert len(linux_locator.provisioned_with) == 1


def test_platform_locator_falls_back_to_not_provided(recording_console):
    """Check that platform locator falls back to not provided."""
    dispatcher = PlatformLocator("fake", {"linux": _locator("/opt/fake-linux")})
    cfg = SimpleNamespace(platform="windows")

    assert dispatcher.locate(cfg) is None
    assert dispatcher.provision(cfg, dry_run=False) is True
    assert recording_console.texts("info") == ["fake is not provided on windows."]


def test_not_provided_always_locates_nothing_and_reports_success(recording_console):
    """Check that not provided always locates nothing and reports success."""
    locator = NotProvided("fake", "windows")
    cfg = SimpleNamespace(platform="windows")
    assert locator.locate(cfg) is None
    assert locator.provision(cfg, dry_run=True) is True
    assert recording_console.texts("info") == ["fake is not provided on windows."]
