# __init__.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Package managers: one class per underlying tool, behind :class:`IPackageManager`."""

from __future__ import annotations

from ..system import ensure_intel_oneapi_repo
from .base import IPackageManager, refresh_windows_path
from .direct_download import (
    WINGET_ID_TO_CMD,
    DirectDownloadWindowsManager,
    download,
    tools_dir,
)
from .github_release import (
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
    "refresh_windows_path",
    "download",
    "gh_tagged_asset",
    "tools_dir",
]
