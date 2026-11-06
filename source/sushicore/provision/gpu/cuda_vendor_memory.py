# cuda_vendor_memory.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The index and the installer behind :class:`CudaVendor`, held in memory."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Mapping

from .cuda_release import RedistRelease, Version
from .cuda_toolkit_installer import ToolkitInstallError


class InMemoryRedistIndex:
    """Publishes fixed versions, each with a release that holds no archive.

    Args:
        versions: The published versions, newest first.
    """

    def __init__(self, versions: Iterable[Version]) -> None:
        """Copy *versions*."""
        self._versions = list(versions)

    def versions(self) -> list[Version]:
        """Return the published versions, newest first."""
        return list(self._versions)

    def release(self, version: Version, platform_key: str) -> RedistRelease:
        """Return an empty release of *version*."""
        return RedistRelease(version, {})


class InMemoryRedistInstaller:
    """Answers the compiler architectures of each major and records installs.

    Args:
        architectures: The architectures the compilers of each major version build for.
        broken: Versions whose compiler does not run.
        base_dir: The folder releases would be installed under; it is only named.

    Attributes:
        installed: The label of each release ``install`` was given.
    """

    def __init__(self, architectures: Mapping[int, frozenset[str]], *,
                 broken: Iterable[Version] = (), base_dir: Path = Path("toolkits")) -> None:
        """Start with nothing installed."""
        self.base_dir = base_dir
        self.installed: list[str] = []
        self._architectures = dict(architectures)
        self._broken = set(broken)

    def probe_architectures(self, release: RedistRelease) -> frozenset[str]:
        """Return what the release's major builds for, or raise when its compiler is broken."""
        if release.version in self._broken:
            raise ToolkitInstallError("nvcc did not run")
        return self._architectures[release.version[0]]

    def install(self, release: RedistRelease) -> Path:
        """Record the install and return the release folder."""
        self.installed.append(release.label)
        return self.base_dir / release.label
