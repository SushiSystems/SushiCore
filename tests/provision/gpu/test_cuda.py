# test_cuda.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests the CUDA backend spec and its toolkit locator."""

from __future__ import annotations

import pathlib
from types import SimpleNamespace

import pytest

from sushicore.provision.gpu.backend import ToolkitInstall
from sushicore.provision.gpu.cuda import cuda_spec
from sushicore.provision.gpu.toolkit_vendor_memory import InMemoryToolkitVendor

pytestmark = pytest.mark.small


def test_cuda_names_the_toolkit_root_to_the_adapter_build():
    """Check that the toolkit root reaches the adapter build as CUDAToolkit_ROOT."""
    root = pathlib.Path("/opt/cuda")
    install = ToolkitInstall(root=root, version="12.6")

    assert cuda_spec().adapter_definitions(install) == {"CUDAToolkit_ROOT": str(root)}


@pytest.mark.parametrize("platform", ["linux", "windows"])
def test_cuda_locates_through_the_vendor_on_linux_and_windows(platform):
    """Check that both CUDA platforms find the toolkit the vendor's root variable names."""
    root = pathlib.Path("cuda-root")
    vendor = InMemoryToolkitVendor(pathlib.Path("toolkits"), toolkit_roots=[root])
    spec = cuda_spec(vendor, process_environment={vendor.root_variable: str(root)})

    install = spec.locator.locate(SimpleNamespace(platform=platform))

    assert install == ToolkitInstall(root=root, version=None)
