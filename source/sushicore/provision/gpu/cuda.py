# cuda.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""The CUDA backend: the release chosen for this machine's cards, and its adapter build.

No CUDA version is written here; :class:`CudaVendor` chooses it from the hardware. The reasoning
is in docs/design/GPU_TOOLKIT_SELECTION/README.md.
"""

from __future__ import annotations

from .backend import GpuBackendSpec, PlatformLocator, ToolkitInstall
from .chosen_toolkit_locator import ChosenToolkitLocator
from .cuda_vendor import CudaVendor


def _adapter_definitions(install: ToolkitInstall) -> dict[str, str]:
    """Name the CUDA toolkit root to the Unified Runtime CUDA adapter build."""
    return {"CUDAToolkit_ROOT": str(install.root)}


CUDA = GpuBackendSpec(
    vendor="cuda",
    probe_vendor="nvidia",
    locator=PlatformLocator("CUDA", dict.fromkeys(
        ("linux", "windows"), ChosenToolkitLocator(CudaVendor()))),
    adapter_option="UR_BUILD_ADAPTER_CUDA",
    adapter_definitions=_adapter_definitions,
    adapter_target="ur_adapter_cuda",
    adapter_binaries=("ur_adapter_cuda", "umf"),
)
