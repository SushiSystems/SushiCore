# rocm_vendor.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""AMD's answers to the toolkit vendor contract: the newest ROCm SDK tarball whose family covers
every AMD card, from AMD's tarball listing."""

from __future__ import annotations

import os
import shutil
import typing
from pathlib import Path

from .amd_hardware import AmdHardware, query_hardware
from .rocm_package import RocmPackage
from .rocm_selection import select_package
from .rocm_tarball_index import RocmIndexError, RocmTarballIndex
from .rocm_toolkit_installer import RocmTarballInstaller, is_rocm_root

#: Where AMD's own packages install ROCm.
K_SYSTEM_ROOT = Path("/opt/rocm")


@typing.final
class RocmVendor:
    """Chooses and installs ROCm releases on Linux.

    Args:
        hardware: Returns the AMD cards, or None without the amdgpu driver.
        index: AMD's tarball listing.
        installer: Downloads and unpacks tarballs.
    """

    def __init__(self,
                 hardware: typing.Callable[[], AmdHardware | None] = query_hardware,
                 index: RocmTarballIndex | None = None,
                 installer: RocmTarballInstaller | None = None) -> None:
        """Store the collaborators, defaulting to the real ones."""
        self._hardware = hardware
        self._index = index or RocmTarballIndex()
        self._installer = installer or RocmTarballInstaller()

    @property
    def name(self) -> str:
        """Return ``ROCm``."""
        return "ROCm"

    @property
    def root_variable(self) -> str:
        """Return ``ROCM_PATH``, which SushiRuntime's locator reads first."""
        return "ROCM_PATH"

    @property
    def override_variable(self) -> str:
        """Return the variable that names a ROCm release in place of the choice."""
        return "SUSHISYSTEMS_ROCM_RELEASE"

    @property
    def platform_key(self) -> str:
        """Return ``linux``; AMD's listing also has ``windows``, which no adapter uses yet."""
        return "linux"

    @property
    def toolkits_dir(self) -> Path:
        """Return ``<home>/rocm``."""
        return self._installer.base_dir

    def query_hardware(self) -> AmdHardware | None:
        """Return the AMD cards."""
        return self._hardware()

    def choose(self, hardware: AmdHardware) -> str | None:
        """Return the newest tarball whose family covers every card."""
        chosen = select_package(hardware, self._index.packages(self.platform_key))
        return chosen.label if chosen is not None else None

    def resolve_override(self, text: str) -> str:
        """Return the tarball *text* names: a release or its prefix, such as ``7.12``, with an
        optional family, such as ``7.12.0-gfx110X-all``. Without a family, the one the
        hardware needs is taken."""
        version_text, _, family = text.partition("-")
        try:
            wanted = tuple(int(part) for part in version_text.split("."))
        except ValueError as error:
            raise RocmIndexError(f"{text} is not a ROCm release") from error
        matching = [p for p in self._index.packages(self.platform_key)
                    if p.version[:len(wanted)] == wanted and (not family or p.family == family)]
        hardware = self._hardware()
        chosen = select_package(hardware, matching) if hardware is not None else None
        if chosen is None and family and matching:
            chosen = matching[0]
        if chosen is None:
            raise RocmIndexError(f"AMD publishes no ROCm tarball for these cards matching {text}")
        return chosen.label

    def is_installed(self, label: str) -> bool:
        """Report whether the release is unpacked."""
        return self._installer.is_installed(label)

    def root_of(self, label: str) -> Path:
        """Return ``<home>/rocm/<label>``."""
        return self._installer.root_of(label)

    def install(self, label: str) -> Path:
        """Download and unpack the tarball labelled *label*."""
        return self._installer.install(self._package(label))

    def discard_downloads(self) -> None:
        """Delete tarballs left by an install that did not finish."""
        self._installer.discard_downloads()

    def is_toolkit_root(self, root: Path) -> bool:
        """Report whether *root* holds the HIP runtime headers."""
        return is_rocm_root(root)

    def find_system_toolkit(self) -> Path | None:
        """Return ``/opt/rocm`` when AMD's packages installed ROCm there."""
        if (shutil.which("hipcc") or shutil.which("rocminfo")) and os.name != "nt":
            return K_SYSTEM_ROOT if is_rocm_root(K_SYSTEM_ROOT) else None
        return None

    def _package(self, label: str) -> RocmPackage:
        """Return the published tarball labelled *label*."""
        for package in self._index.packages(self.platform_key):
            if package.label == label:
                return package
        raise RocmIndexError(f"AMD no longer lists the ROCm tarball {label}")

