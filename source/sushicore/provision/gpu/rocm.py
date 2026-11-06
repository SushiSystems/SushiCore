# rocm.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The ROCm backend: the release chosen for this machine's AMD cards, and its adapter build.

Linux only: intel/llvm ships no HIP adapter on Windows, so nothing there would use the SDK.
The reasoning is in docs/design/GPU_TOOLKIT_SELECTION/README.md.
"""

from __future__ import annotations

import typing

from .backend import GpuBackendSpec, PlatformLocator, ToolkitInstall
from .chosen_toolkit_locator import ChosenToolkitLocator
from .rocm_vendor import RocmVendor
from .toolkit_vendor import ToolkitVendor


def _adapter_definitions(install: ToolkitInstall) -> dict[str, str]:
    """Name the ROCm install directory to the Unified Runtime HIP adapter build."""
    return {"UR_HIP_ROCM_DIR": str(install.root)}


def rocm_spec(vendor: ToolkitVendor | None = None, *,
              process_environment: typing.MutableMapping[str, str] | None = None) -> GpuBackendSpec:
    """Return the ROCm backend spec.

    Args:
        vendor: Answers the vendor questions; a :class:`RocmVendor` when None.
        process_environment: The variables of this process the locator reads and writes;
            :data:`os.environ` when None.
    """
    chosen = ChosenToolkitLocator(vendor or RocmVendor(), process_environment=process_environment)
    return GpuBackendSpec(
        vendor="rocm",
        probe_vendor="amd",
        locator=PlatformLocator("ROCm", {"linux": chosen}),
        adapter_option="UR_BUILD_ADAPTER_HIP",
        adapter_definitions=_adapter_definitions,
        adapter_target="ur_adapter_hip",
        adapter_binaries=("ur_adapter_hip", "umf"),
    )


ROCM = rocm_spec()
