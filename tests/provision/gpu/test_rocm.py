# test_rocm.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests the ROCm backend spec and its toolkit locator."""

from __future__ import annotations

import pathlib

from types import SimpleNamespace

import pytest

from sushicore.provision.gpu.backend import ToolkitInstall

from sushicore.provision.gpu.rocm import ROCM



pytestmark = pytest.mark.medium



def test_rocm_spec_declares_the_adapter_build_inputs():
    """Check that rocm spec declares the adapter build inputs."""
    assert ROCM.vendor == "rocm"
    assert ROCM.probe_vendor == "amd"
    assert ROCM.adapter_option == "UR_BUILD_ADAPTER_HIP"
    assert ROCM.adapter_target == "ur_adapter_hip"
    assert ROCM.adapter_binaries == ("ur_adapter_hip", "umf")
    root = pathlib.Path("/opt/rocm")
    install = ToolkitInstall(root=root, version=None)
    assert ROCM.adapter_definitions(install) == {"UR_HIP_ROCM_DIR": str(root)}



def test_rocm_locator_takes_the_root_rocm_path_names(monkeypatch, tmp_path):
    """Check that a ROCM_PATH holding the HIP headers is the toolkit found."""
    header = tmp_path / "include" / "hip" / "hip_runtime.h"
    header.parent.mkdir(parents=True)
    header.write_text("")
    monkeypatch.setenv("ROCM_PATH", str(tmp_path))

    install = ROCM.locator.locate(SimpleNamespace(platform="linux"))

    assert install == ToolkitInstall(root=pathlib.Path(str(tmp_path)), version=None)
