# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
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
from sushicore.provision.gpu.registry import Registry


class _FakeLocator:
    """A locator that reports a fixed install and records provision calls."""

    def __init__(self, root: str) -> None:
        """Store the install root this fake locator always reports."""
        self._root = root
        self.provisioned = False

    def locate(self, cfg):
        """Return a fixed ToolkitInstall rooted at the stored path."""
        return ToolkitInstall(root=pathlib.Path(self._root), version="1.0")

    def provision(self, cfg, dry_run: bool) -> bool:
        """Record that provisioning was requested and report success."""
        self.provisioned = True
        return True


def _fake_spec(vendor: str = "fake", probe_vendor: str = "fakevendor",
               locator=None) -> GpuBackendSpec:
    """Build one GpuBackendSpec whose fields carry no real toolkit behaviour."""
    return GpuBackendSpec(
        vendor=vendor,
        probe_vendor=probe_vendor,
        locator=locator or _FakeLocator("/opt/fake"),
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


def test_a_duplicate_vendor_name_is_refused():
    """Check that a duplicate vendor name is refused."""
    with pytest.raises(ValueError):
        Registry((_fake_spec(vendor="fake", probe_vendor="a"),
                  _fake_spec(vendor="fake", probe_vendor="b")))


def test_a_duplicate_probe_vendor_is_refused():
    """Check that a duplicate probe vendor is refused."""
    with pytest.raises(ValueError):
        Registry((_fake_spec(vendor="a", probe_vendor="fakevendor"),
                  _fake_spec(vendor="b", probe_vendor="fakevendor")))


def test_platform_locator_dispatches_to_the_matching_platform():
    """Check that platform locator dispatches to the matching platform."""
    linux_locator = _FakeLocator("/opt/fake-linux")
    dispatcher = PlatformLocator("fake", {"linux": linux_locator})
    cfg = SimpleNamespace(platform="linux")

    install = dispatcher.locate(cfg)
    assert install == ToolkitInstall(root=pathlib.Path("/opt/fake-linux"), version="1.0")

    assert dispatcher.provision(cfg, dry_run=False) is True
    assert linux_locator.provisioned is True


def test_platform_locator_falls_back_to_not_provided(recording_console):
    """Check that platform locator falls back to not provided."""
    dispatcher = PlatformLocator("fake", {"linux": _FakeLocator("/opt/fake-linux")})
    cfg = SimpleNamespace(platform="windows")

    assert dispatcher.locate(cfg) is None
    assert dispatcher.provision(cfg, dry_run=False) is True


def test_not_provided_always_locates_nothing_and_reports_success(recording_console):
    """Check that not provided always locates nothing and reports success."""
    locator = NotProvided("fake", "windows")
    cfg = SimpleNamespace(platform="windows")
    assert locator.locate(cfg) is None
    assert locator.provision(cfg, dry_run=True) is True


def test_platform_locator_works_with_a_plain_config_stand_in():
    """Check that platform locator works with a plain config stand in."""
    dispatcher = PlatformLocator("fake", {"linux": _FakeLocator("/opt/fake-linux")})
    cfg = SimpleNamespace(platform="linux")

    install = dispatcher.locate(cfg)

    assert install is not None
    assert install.root == pathlib.Path("/opt/fake-linux")
