# test_toolkit_vendor.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests the protocol every toolkit vendor follows."""

import pytest

from sushicore.provision.gpu.cuda_vendor import CudaVendor
from sushicore.provision.gpu.rocm_vendor import RocmVendor
from sushicore.provision.gpu.toolkit_vendor import ToolkitSourceError, ToolkitVendor

pytestmark = pytest.mark.small

K_MEMBERS = tuple(
    name for name in vars(ToolkitVendor)
    if not name.startswith("_") and name not in {"register"}
)


def test_the_protocol_names_every_member_a_vendor_needs():
    assert {"name", "choose", "install", "is_toolkit_root"} <= set(K_MEMBERS)


@pytest.mark.parametrize("vendor", [CudaVendor, RocmVendor])
def test_every_vendor_defines_every_member_of_the_protocol(vendor):
    assert [name for name in K_MEMBERS if not hasattr(vendor, name)] == []


def test_a_source_error_is_an_exception():
    assert issubclass(ToolkitSourceError, Exception)
