# __init__.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The targets provision runs for and the choice between them."""

from __future__ import annotations

from .base import K_LINUX, K_WINDOWS, ITarget
from .current import target_for_platform, target_of
from .linux import K_LINUX_MANAGERS, LinuxTarget
from .windows import WindowsTarget

__all__ = [
    "ITarget", "K_LINUX", "K_LINUX_MANAGERS", "K_WINDOWS", "LinuxTarget", "WindowsTarget",
    "target_for_platform", "target_of",
]
