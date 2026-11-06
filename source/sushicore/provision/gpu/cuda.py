# cuda.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The CUDA backend: the release chosen for this machine's cards, and its adapter build.

No CUDA version is written here; :class:`CudaVendor` chooses it from the hardware. The reasoning
is in docs/design/GPU_TOOLKIT_SELECTION/README.md.
"""

from __future__ import annotations

import typing

from .backend import GpuBackendSpec, PlatformLocator, ToolkitInstall
from .chosen_toolkit_locator import ChosenToolkitLocator
from .cuda_vendor import CudaVendor
from .toolkit_vendor import ToolkitVendor


def _adapter_definitions(install: ToolkitInstall) -> dict[str, str]:
    """Name the CUDA toolkit root to the Unified Runtime CUDA adapter build."""
    return {"CUDAToolkit_ROOT": str(install.root)}


def cuda_spec(vendor: ToolkitVendor | None = None, *,
              process_environment: typing.MutableMapping[str, str] | None = None) -> GpuBackendSpec:
    """Return the CUDA backend spec.

    Args:
        vendor: Answers the vendor questions; a :class:`CudaVendor` when None.
        process_environment: The variables of this process the locator reads and writes;
            :data:`os.environ` when None.
    """
    chosen = ChosenToolkitLocator(vendor or CudaVendor(), process_environment=process_environment)
    return GpuBackendSpec(
        vendor="cuda",
        probe_vendor="nvidia",
        locator=PlatformLocator("CUDA", dict.fromkeys(("linux", "windows"), chosen)),
        adapter_option="UR_BUILD_ADAPTER_CUDA",
        adapter_definitions=_adapter_definitions,
        adapter_target="ur_adapter_cuda",
        adapter_binaries=("ur_adapter_cuda", "umf"),
    )


CUDA = cuda_spec()
