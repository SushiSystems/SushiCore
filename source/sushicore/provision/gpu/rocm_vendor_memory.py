# rocm_vendor_memory.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The tarball index and the installer behind :class:`RocmVendor`, held in memory."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from .rocm_package import RocmPackage


class InMemoryTarballIndex:
    """Lists fixed tarballs for every platform.

    Args:
        packages: The tarballs, newest first.
    """

    def __init__(self, packages: Iterable[RocmPackage]) -> None:
        """Copy *packages*."""
        self._packages = list(packages)

    def packages(self, platform: str) -> list[RocmPackage]:
        """Return the tarballs, newest first."""
        return list(self._packages)


class InMemoryTarballInstaller:
    """Records the tarballs it is asked to install and unpacks nothing.

    Args:
        base_dir: The folder releases would be installed under; it is only named.

    Attributes:
        installed: The tarball of each install, in order.
    """

    def __init__(self, base_dir: Path = Path("toolkits")) -> None:
        """Start with nothing installed."""
        self.base_dir = base_dir
        self.installed: list[RocmPackage] = []

    def install(self, package: RocmPackage) -> Path:
        """Record *package* and return its label as a path."""
        self.installed.append(package)
        return Path(package.label)
