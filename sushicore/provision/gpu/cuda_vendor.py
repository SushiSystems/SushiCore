# cuda_vendor.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""NVIDIA's answers to the toolkit vendor contract: the newest CUDA release the driver runs
whose nvcc builds for every card, from NVIDIA's redistributable archives."""

from __future__ import annotations

import glob
import os
import platform as host_platform
import shutil
import typing
from pathlib import Path

from .._output import console
from .cuda_hardware import NvidiaHardware, query_hardware
from .cuda_redist import RedistError, RedistIndex
from .cuda_release import Version, format_version, parse_version
from .cuda_selection import select_release
from .cuda_toolkit_installer import (
    RedistToolkitInstaller,
    ToolkitInstallError,
    nvcc_in,
)

# Neither the apt CUDA toolkit nor a manual install adds itself to PATH.
K_NVCC_GLOBS_LINUX = (
    "/usr/local/cuda/bin/nvcc",
    "/usr/local/cuda-*/bin/nvcc",
)


@typing.final
class CudaVendor:
    """Chooses and installs CUDA releases.

    Args:
        hardware: Returns the cards and the driver's CUDA ceiling, or None without a driver.
        index: NVIDIA's redistributable index.
        installer: Downloads and unpacks releases.
    """

    def __init__(self,
                 hardware: typing.Callable[[], NvidiaHardware | None] = query_hardware,
                 index: RedistIndex | None = None,
                 installer: RedistToolkitInstaller | None = None) -> None:
        """Store the collaborators, defaulting to the real ones."""
        self._hardware = hardware
        self._index = index or RedistIndex()
        self._installer = installer or RedistToolkitInstaller()

    @property
    def name(self) -> str:
        """Return ``CUDA``."""
        return "CUDA"

    @property
    def root_variable(self) -> str:
        """Return ``CUDA_PATH``, which SushiRuntime's locator reads first."""
        return "CUDA_PATH"

    @property
    def override_variable(self) -> str:
        """Return the variable that names a CUDA release in place of the choice."""
        return "SUSHISYSTEMS_CUDA_RELEASE"

    @property
    def platform_key(self) -> str:
        """Return this machine's key in NVIDIA's index, such as ``windows-x86_64``."""
        if os.name == "nt":
            return "windows-x86_64"
        machine = host_platform.machine().lower()
        return "linux-sbsa" if machine in ("aarch64", "arm64") else "linux-x86_64"

    @property
    def toolkits_dir(self) -> Path:
        """Return ``<home>/cuda``."""
        return self._installer.base_dir

    def query_hardware(self) -> NvidiaHardware | None:
        """Return the cards and the driver's ceiling."""
        return self._hardware()

    def choose(self, hardware: NvidiaHardware) -> str | None:
        """Return the newest release the driver runs whose nvcc builds every card."""
        chosen = select_release(hardware, self._index.versions(), self._architectures)
        return format_version(chosen) if chosen is not None else None

    def resolve_override(self, text: str) -> str:
        """Return the newest published release that *text* names or prefixes."""
        try:
            wanted = parse_version(text)
        except ValueError as error:
            raise RedistError(f"{text} is not a CUDA version") from error
        for version in self._index.versions():
            if version[:len(wanted)] == wanted:
                return format_version(version)
        raise RedistError(f"NVIDIA publishes no CUDA release matching {text}")

    def is_installed(self, label: str) -> bool:
        """Report whether the release's nvcc is in place."""
        return self._installer.is_installed(label)

    def root_of(self, label: str) -> Path:
        """Return ``<home>/cuda/<label>``."""
        return self._installer.root_of(label)

    def install(self, label: str) -> Path:
        """Download, verify and unpack the release."""
        return self._installer.install(self._index.release(parse_version(label),
                                                           self.platform_key))

    def discard_downloads(self) -> None:
        """Delete the nvcc archives kept from probing."""
        self._installer.discard_downloads()

    def is_toolkit_root(self, root: Path) -> bool:
        """Report whether *root* holds nvcc."""
        return nvcc_in(root).is_file()

    def find_system_toolkit(self) -> Path | None:
        """Return the root of an nvcc on PATH, or under a well-known Linux prefix."""
        nvcc = shutil.which("nvcc") or ("" if os.name == "nt" else _glob_nvcc())
        return Path(nvcc).resolve().parent.parent if nvcc else None

    def _architectures(self, version: Version) -> frozenset[str]:
        """Return what *version*'s nvcc builds for; an unreadable one builds for nothing."""
        console.info(f"Asking the CUDA {format_version(version)} compiler which cards it "
                     "builds for ...")
        try:
            return self._installer.probe_architectures(
                self._index.release(version, self.platform_key))
        except (RedistError, ToolkitInstallError) as error:
            console.warn(f"CUDA {format_version(version)} skipped: {error}")
            return frozenset()


def _glob_nvcc() -> str:
    """Return the newest nvcc found under the well-known Linux install globs."""
    for pattern in K_NVCC_GLOBS_LINUX:
        hits = sorted(glob.glob(pattern))
        if hits:
            return hits[-1]
    return ""
