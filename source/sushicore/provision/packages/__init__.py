# __init__.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Package managers: one class per underlying tool, behind :class:`IPackageManager`."""

from __future__ import annotations

from ..intel_oneapi_repo import ensure_intel_oneapi_repo
from .base import IPackageManager
from .compat import (
    gh_latest_asset,
    gh_latest_asset_including_prerelease,
    gh_latest_release_asset,
    prime_sudo,
    run,
)
from .direct_download import (
    WINGET_ID_TO_CMD,
    DirectDownloadWindowsManager,
    download,
    downloader,
    tools_dir,
)
from .github_release import (
    gh_tagged_asset,
)
from .gpu_stack import install_gpu_stack
from .apt_manager import AptManager
from .dnf_manager import DnfManager
from .linux_manager import LinuxPackageManager
from .pacman_manager import PacmanManager
from .yum_manager import YumManager
from .zypper_manager import ZypperManager
from .vcpkg import VcpkgManager
from .windows_path import refresh_windows_path
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
    "refresh_windows_path",
    "download",
    "downloader",
    "gh_tagged_asset",
    "tools_dir",
    "gh_latest_asset",
    "gh_latest_asset_including_prerelease",
    "gh_latest_release_asset",
    "prime_sudo",
    "run",
]
