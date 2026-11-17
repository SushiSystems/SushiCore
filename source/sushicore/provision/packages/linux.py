# linux.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The deprecated ``sushicore.provision.packages.linux`` module; each manager now has its own module."""

from __future__ import annotations

from ..deprecated_name import warn_deprecated
from .apt_manager import AptManager
from .dnf_manager import DnfManager
from .linux_manager import LinuxPackageManager
from .pacman_manager import PacmanManager
from .yum_manager import YumManager
from .zypper_manager import ZypperManager

warn_deprecated(
    "sushicore.provision.packages.linux",
    "sushicore.provision.packages, or the module named after each manager "
    "(linux_manager, apt_manager, dnf_manager, yum_manager, pacman_manager, zypper_manager)")

__all__ = [
    "AptManager",
    "DnfManager",
    "LinuxPackageManager",
    "PacmanManager",
    "YumManager",
    "ZypperManager",
]
