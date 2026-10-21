# rocm.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""The ROCm backend: the release chosen for this machine's AMD cards, and its adapter build.

Linux only: intel/llvm ships no HIP adapter on Windows, so nothing there would use the SDK.
The reasoning is in docs/design/GPU_TOOLKIT_SELECTION/README.md.
"""

from __future__ import annotations

from .backend import GpuBackendSpec, PlatformLocator, ToolkitInstall
from .chosen_toolkit_locator import ChosenToolkitLocator
from .rocm_vendor import RocmVendor


def _adapter_definitions(install: ToolkitInstall) -> dict[str, str]:
    """Name the ROCm install directory to the Unified Runtime HIP adapter build."""
    return {"UR_HIP_ROCM_DIR": str(install.root)}


ROCM = GpuBackendSpec(
    vendor="rocm",
    probe_vendor="amd",
    locator=PlatformLocator("ROCm", {"linux": ChosenToolkitLocator(RocmVendor())}),
    adapter_option="UR_BUILD_ADAPTER_HIP",
    adapter_definitions=_adapter_definitions,
    adapter_target="ur_adapter_hip",
    adapter_binaries=("ur_adapter_hip", "umf"),
)
