# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""The ROCm backend: AMD's HIP toolkit, located and provisioned on Linux."""

from __future__ import annotations

import os
import pathlib
import shutil
import typing

from .._output import console
from ..system import is_root, os_release, sudo_bash
from .backend import GpuBackendSpec, PlatformLocator, ToolkitInstall

if typing.TYPE_CHECKING:
    from ..config import ProvisionConfig


class LinuxRocmLocator:
    """Finds and installs AMD ROCm (HIP runtime + dev) from AMD's official apt repo."""

    def locate(self, cfg: "ProvisionConfig") -> ToolkitInstall | None:
        """Return ROCM_PATH, else /opt/rocm, when hipcc or rocminfo is on PATH."""
        if not (shutil.which("hipcc") or shutil.which("rocminfo")):
            return None
        root = os.environ.get("ROCM_PATH") or "/opt/rocm"
        return ToolkitInstall(root=pathlib.Path(root), version=None)

    def provision(self, cfg: "ProvisionConfig", dry_run: bool) -> bool:
        """Install AMD ROCm (HIP runtime + dev) from AMD's official apt repo (Ubuntu/Debian)."""
        if self.locate(cfg) is not None:
            console.info("ROCm already present.")
            return True
        rel = os_release()
        codename = rel.get("VERSION_CODENAME", "")
        if rel.get("ID", "").lower() not in ("ubuntu", "debian") or not codename:
            console.warn("Unrecognised distro for the AMD ROCm repo; install ROCm "
                         "manually (https://rocm.docs.amd.com).")
            return False
        sudo = "" if is_root() else "sudo "
        steps = (
            f"{sudo}mkdir -p --mode=0755 /etc/apt/keyrings && "
            f"curl -fsSL https://repo.radeon.com/rocm/rocm.gpg.key "
            f"| {sudo}gpg --dearmor -o /etc/apt/keyrings/rocm.gpg && "
            f'echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/rocm.gpg] '
            f'https://repo.radeon.com/rocm/apt/latest {codename} main" '
            f"| {sudo}tee /etc/apt/sources.list.d/rocm.list && "
            f"{sudo}apt-get update && "
            f"{sudo}apt-get install -y rocm-hip-runtime-dev"
        )
        if not sudo_bash(steps, dry_run):
            console.warn("ROCm install failed. Install it manually "
                         "(https://rocm.docs.amd.com); the build will otherwise fall "
                         "back to the CPU/OpenCL path.")
            return False
        return True


def _adapter_definitions(install: ToolkitInstall) -> dict[str, str]:
    """Name the ROCm install directory to the Unified Runtime HIP adapter build."""
    return {"UR_HIP_ROCM_DIR": str(install.root)}


ROCM = GpuBackendSpec(
    vendor="rocm",
    probe_vendor="amd",
    locator=PlatformLocator("ROCm", {
        "linux": LinuxRocmLocator(),
    }),
    adapter_option="UR_BUILD_ADAPTER_HIP",
    adapter_definitions=_adapter_definitions,
    adapter_target="ur_adapter_hip",
    adapter_binaries=("ur_adapter_hip", "umf"),
)
