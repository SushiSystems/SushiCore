# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""The Level Zero backend: Intel's GPU compute stack, located on Linux."""

from __future__ import annotations

import ctypes.util
import pathlib
import typing

from .._output import console
from ..system import ensure_intel_oneapi_repo, is_root, sudo_bash
from .backend import GpuBackendSpec, PlatformLocator, ToolkitInstall

if typing.TYPE_CHECKING:
    from ..config import ProvisionConfig

# Fallback directories checked when ctypes.util.find_library finds nothing.
_ZE_LOADER_LIB_DIRS = (
    "/usr/lib/x86_64-linux-gnu",
    "/usr/lib64",
    "/usr/lib",
)
_ZE_LOADER_GLOB = "libze_loader.so*"


def _find_ze_loader() -> pathlib.Path | None:
    """Return the directory holding libze_loader, or None when it is absent."""
    found = ctypes.util.find_library("ze_loader")
    if found:
        path = pathlib.PurePosixPath(found)
        return pathlib.Path(str(path.parent)) if path.is_absolute() else pathlib.Path("/usr/lib")
    for directory in _ZE_LOADER_LIB_DIRS:
        if next(pathlib.Path(directory).glob(_ZE_LOADER_GLOB), None) is not None:
            return pathlib.Path(directory)
    return None


class LinuxLevelZeroLocator:
    """Finds and installs the Intel GPU compute stack (Level Zero + OpenCL)."""

    def locate(self, cfg: "ProvisionConfig") -> ToolkitInstall | None:
        """Return the directory holding the Level Zero loader, or None."""
        directory = _find_ze_loader()
        if directory is None:
            return None
        return ToolkitInstall(root=directory, version=None)

    def provision(self, cfg: "ProvisionConfig", dry_run: bool) -> bool:
        """Install the Intel GPU compute stack (Level Zero + OpenCL) for Intel GPUs."""
        if not ensure_intel_oneapi_repo(dry_run):
            return False
        sudo = "" if is_root() else "sudo "
        steps = (
            f"{sudo}apt-get update && "
            f"{sudo}apt-get install -y level-zero intel-oneapi-runtime-opencl "
            f"intel-oneapi-runtime-libs"
        )
        if not sudo_bash(steps, dry_run):
            console.warn("Intel GPU runtime install failed; the build will fall back "
                         "to the CPU/OpenCL path.")
            return False
        return True


LEVEL_ZERO = GpuBackendSpec(
    vendor="level_zero",
    probe_vendor="intel",
    locator=PlatformLocator("Level Zero", {
        "linux": LinuxLevelZeroLocator(),
    }),
    adapter_option="UR_BUILD_ADAPTER_L0",
    adapter_definitions=lambda install: {},
    adapter_target="ur_adapter_level_zero",
    adapter_binaries=("ur_adapter_level_zero", "umf"),
)
