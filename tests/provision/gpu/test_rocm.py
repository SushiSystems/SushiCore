# test_rocm.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests the ROCm backend spec and its toolkit locator."""

from __future__ import annotations

import pathlib
from types import SimpleNamespace

import pytest

from sushicore.provision.gpu.backend import ToolkitInstall
from sushicore.provision.gpu.rocm import rocm_spec
from sushicore.provision.gpu.toolkit_vendor_memory import InMemoryToolkitVendor

pytestmark = pytest.mark.small


def test_rocm_names_the_install_directory_to_the_adapter_build():
    """Check that the install directory reaches the adapter build as UR_HIP_ROCM_DIR."""
    root = pathlib.Path("/opt/rocm")
    install = ToolkitInstall(root=root, version=None)

    assert rocm_spec().adapter_definitions(install) == {"UR_HIP_ROCM_DIR": str(root)}


def test_rocm_locates_through_the_vendor_on_linux():
    """Check that Linux finds the toolkit the vendor's root variable names."""
    root = pathlib.Path("rocm-root")
    vendor = InMemoryToolkitVendor(pathlib.Path("toolkits"), toolkit_roots=[root])
    spec = rocm_spec(vendor, process_environment={vendor.root_variable: str(root)})

    install = spec.locator.locate(SimpleNamespace(platform="linux"))

    assert install == ToolkitInstall(root=root, version=None)
