# current.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Picks the target a run provisions for; the one place that reads the platform name."""

from __future__ import annotations

from ..config import ProvisionConfig
from .base import ITarget
from .linux import LinuxTarget
from .windows import WindowsTarget


def target_for_platform(platform: str) -> ITarget:
    """Return the target named *platform*: Windows for ``windows``, Linux for any other name."""
    return WindowsTarget() if platform == "windows" else LinuxTarget()


def target_of(cfg: ProvisionConfig) -> ITarget:
    """Return the target the run configured by *cfg* provisions for."""
    return target_for_platform(cfg.platform)
