# test_install_location.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The finder contract is what a GPU locator and a SYCL toolchain both answer."""

from __future__ import annotations

import pytest

from sushicore.provision.gpu.backend_memory import InMemoryToolkitLocator
from sushicore.provision.install_location import ToolkitFinder
from sushicore.provision.toolchains.registry import DEFAULT_REGISTRY

pytestmark = pytest.mark.small


def test_a_gpu_locator_and_every_toolchain_are_toolkit_finders():
    """Check that the in-memory GPU locator and each declared toolchain satisfy ToolkitFinder."""
    finders = [InMemoryToolkitLocator(None), *DEFAULT_REGISTRY.all()]
    assert [isinstance(finder, ToolkitFinder) for finder in finders] == [True] * 4
