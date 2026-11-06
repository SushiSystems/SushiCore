# test_toolkit_vendor.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests the protocol every toolkit vendor follows."""

from pathlib import Path

import pytest

from sushicore.provision.gpu.cuda_vendor import CudaVendor
from sushicore.provision.gpu.rocm_vendor import RocmVendor
from sushicore.provision.gpu.toolkit_vendor import ToolkitVendor
from sushicore.provision.gpu.toolkit_vendor_memory import InMemoryToolkitVendor

pytestmark = pytest.mark.small

K_MEMBERS = tuple(
    name for name in vars(ToolkitVendor)
    if not name.startswith("_") and name not in {"register"}
)


def test_the_protocol_names_every_member_a_vendor_needs():
    assert {"name", "choose", "install", "is_toolkit_root"} <= set(K_MEMBERS)


@pytest.mark.parametrize("member", K_MEMBERS)
@pytest.mark.parametrize("vendor", [CudaVendor, RocmVendor], ids=["cuda", "rocm"])
def test_every_vendor_defines_every_member_of_the_protocol(vendor, member):
    """Check that each real vendor class defines the member."""
    assert hasattr(vendor, member)


def test_the_in_memory_vendor_satisfies_the_protocol():
    """Check that the in-memory vendor passes the runtime protocol check."""
    assert isinstance(InMemoryToolkitVendor(Path("toolkits")), ToolkitVendor)
