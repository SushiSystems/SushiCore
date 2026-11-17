# fragment_types.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Holds the types a dependency fragment is read into: its entries, pins and downloads."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

#: The platform string that selects the vcpkg column; anything else selects apt.
WINDOWS = "windows"


class Status(str, Enum):
    """What is known about one dependency on this machine."""

    #: Its ``check_cmd`` ran and exited 0.
    SATISFIED = "satisfied"
    #: It names no package for this platform, so there is nothing to install.
    NOT_APPLICABLE = "not applicable"
    #: It names a package and nothing here can say whether it is installed.
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class Download:
    """One file an installer downloads for an entry on one platform, fully pinned."""

    #: The entry that declares it.
    name: str
    #: The release the file belongs to, as the vendor names it.
    version: str
    #: The exact address of the file.
    url: str
    #: The lower-case hex SHA-256 the vendor published for the file.
    sha256: str


@dataclass(frozen=True)
class Dependency:
    """One entry of a fragment, as the file declares it."""

    name: str
    description: str = ""
    required: bool = True
    gpu_only: bool = False
    linux_apt: list[str] = field(default_factory=list)
    windows_vcpkg: list[str] = field(default_factory=list)
    check_cmd: list[str] = field(default_factory=list)
    provides: str = ""
    #: Platform to the lower-case hex SHA-256 of the file downloaded for it there.
    sha256: dict[str, str] = field(default_factory=dict)
    #: The release every download of the entry belongs to; empty when it declares none.
    version: str = ""
    #: Platform to the exact address of the file downloaded for it there.
    url: dict[str, str] = field(default_factory=dict)

    def download_for(self, platform: str) -> Download | None:
        """Return the pinned download for *platform*, or None when the entry has none there."""
        if platform not in self.url or platform not in self.sha256:
            return None
        return Download(self.name, self.version, self.url[platform], self.sha256[platform])

    def packages_for(self, platform: str) -> list[str]:
        """Package names for *platform*: the vcpkg ports on Windows, apt elsewhere."""
        return self.windows_vcpkg if platform == WINDOWS else self.linux_apt

    def digest_for(self, platform: str) -> str:
        """Return the SHA-256 pinned for the *platform* download, or '' when none is."""
        return self.sha256.get(platform, "")


@dataclass(frozen=True)
class SushiPin:
    """One Sushi library a module links, pinned to a release tag and its commit."""

    name: str
    #: The release tag, such as ``v0.3.0``.
    version: str
    #: The full 40-hex hash the tag points at.
    commit: str


@dataclass(frozen=True)
class Fragment:
    """What one fragment file declares."""

    dependencies: list[Dependency]
    depends_on: list[str]
    pins: list[SushiPin] = field(default_factory=list)
    #: The command of the module's own CLI, such as ``sr``; empty when the module names none.
    cli: str = ""
    #: Git pathspecs the source hash of a package build leaves out, besides the built-in ones.
    package_exclude: list[str] = field(default_factory=list)
