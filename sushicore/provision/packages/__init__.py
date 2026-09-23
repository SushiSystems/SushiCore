# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Package managers: one class per underlying tool, behind :class:`IPackageManager`."""

from __future__ import annotations

from ..system import ensure_intel_oneapi_repo
from .base import IPackageManager, run, prime_sudo, refresh_windows_path
from .direct_download import (
    WINGET_ID_TO_CMD,
    DirectDownloadWindowsManager,
    download,
    tools_dir,
)
from .github_release import (
    gh_latest_asset,
    gh_latest_asset_including_prerelease,
    gh_latest_release_asset,
    gh_tagged_asset,
)
from .gpu_stack import install_gpu_stack
from .linux import (
    AptManager,
    DnfManager,
    LinuxPackageManager,
    PacmanManager,
    YumManager,
    ZypperManager,
)
from .vcpkg import VcpkgManager
from .winget import WingetManager

__all__ = [
    "IPackageManager",
    "LinuxPackageManager",
    "AptManager",
    "DnfManager",
    "YumManager",
    "PacmanManager",
    "ZypperManager",
    "WingetManager",
    "DirectDownloadWindowsManager",
    "VcpkgManager",
    "WINGET_ID_TO_CMD",
    "ensure_intel_oneapi_repo",
    "install_gpu_stack",
    "prime_sudo",
    "refresh_windows_path",
    "download",
    "gh_latest_asset",
    "gh_latest_asset_including_prerelease",
    "gh_latest_release_asset",
    "gh_tagged_asset",
    "run",
    "tools_dir",
]
