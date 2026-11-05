# test_backend.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests what every GPU backend spec shares."""

from __future__ import annotations

import pathlib
from dataclasses import dataclass
from types import SimpleNamespace

import pytest

from sushicore.provision.gpu.backend import (
    NotProvided,
    PlatformLocator,
    ToolkitInstall,
    ToolkitLocator,
)
from sushicore.provision.gpu.backend_memory import InMemoryToolkitLocator

from sushicore.provision.gpu.cuda import CUDA

from sushicore.provision.gpu.level_zero import LEVEL_ZERO

from sushicore.provision.gpu.rocm import ROCM






@pytest.mark.medium
@pytest.mark.parametrize("spec", [CUDA, ROCM, LEVEL_ZERO])
def test_every_backend_reports_not_provided_on_darwin(spec, recording_console):
    """Check that every backend reports not provided on darwin."""
    cfg = SimpleNamespace(platform="darwin")

    assert spec.locator.locate(cfg) is None
    assert isinstance(spec.locator._for(cfg), NotProvided)
    assert spec.locator.provision(cfg, dry_run=True) is True


@dataclass
class LocatorWorld:
    """A locator under test and the install it is expected to find."""

    locator: ToolkitLocator
    expected: ToolkitInstall | None


class ToolkitLocatorContract:
    """The promises every :class:`ToolkitLocator` keeps; a subclass supplies the world.

    The vendor locators that read the hardware, the registry and the vendor's index are not
    run here: they need a GPU and the network, and the large tier holds their checks.
    """

    def test_locate_returns_the_install_found_on_the_machine(self, world):
        assert world.locator.locate(SimpleNamespace(platform="linux")) == world.expected

    def test_locating_twice_gives_the_same_answer(self, world):
        cfg = SimpleNamespace(platform="linux")
        assert world.locator.locate(cfg) == world.locator.locate(cfg)

    def test_a_dry_run_provision_succeeds_unless_it_failed_fatally(self, world):
        assert world.locator.provision(SimpleNamespace(platform="linux"), dry_run=True) is True


_INSTALL = ToolkitInstall(root=pathlib.Path("/opt/toolkit"), version="1.0")


@pytest.mark.small
class TestInMemoryToolkitLocatorKeepsTheToolkitLocatorContract(ToolkitLocatorContract):
    """The in-memory locator that finds a fixed install."""

    @pytest.fixture
    def world(self):
        return LocatorWorld(InMemoryToolkitLocator(_INSTALL), _INSTALL)


@pytest.mark.medium
class TestNotProvidedKeepsTheToolkitLocatorContract(ToolkitLocatorContract):
    """The locator of a backend the platform does not provide; it prints through the bound console."""

    @pytest.fixture
    def world(self, recording_console):
        return LocatorWorld(NotProvided("CUDA", "linux"), None)


@pytest.mark.medium
class TestPlatformLocatorKeepsTheToolkitLocatorContract(ToolkitLocatorContract):
    """The per-platform dispatcher, falling back to the not-provided locator."""

    @pytest.fixture
    def world(self, recording_console):
        return LocatorWorld(PlatformLocator("CUDA", {}), None)
