# test_cuda.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests the CUDA backend spec and its toolkit locator."""

from __future__ import annotations

import pathlib

from types import SimpleNamespace

import pytest

from sushicore.provision.gpu.backend import ToolkitInstall

from sushicore.provision.gpu.cuda import CUDA

from sushicore.provision.gpu.cuda_toolkit_installer import nvcc_in



pytestmark = pytest.mark.medium



def test_cuda_spec_declares_the_adapter_build_inputs():
    """Check that cuda spec declares the adapter build inputs."""
    assert CUDA.vendor == "cuda"
    assert CUDA.probe_vendor == "nvidia"
    assert CUDA.adapter_option == "UR_BUILD_ADAPTER_CUDA"
    assert CUDA.adapter_target == "ur_adapter_cuda"
    assert CUDA.adapter_binaries == ("ur_adapter_cuda", "umf")
    root = pathlib.Path("/opt/cuda")
    install = ToolkitInstall(root=root, version="12.6")
    assert CUDA.adapter_definitions(install) == {"CUDAToolkit_ROOT": str(root)}



def test_cuda_locator_finds_the_toolkit_from_cuda_path(tmp_path, monkeypatch):
    """Check that the CUDA locator takes the toolkit CUDA_PATH names."""
    (tmp_path / "bin").mkdir()
    (tmp_path / "bin" / nvcc_in(tmp_path).name).write_text("")
    monkeypatch.setenv("CUDA_PATH", str(tmp_path))

    install = CUDA.locator.locate(SimpleNamespace(platform="windows"))

    assert install == ToolkitInstall(root=pathlib.Path(str(tmp_path)), version=None)
