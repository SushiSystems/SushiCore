# steps.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The deprecated ``sushicore.provision.steps`` module; each step now has its own module."""

from __future__ import annotations

import warnings

from .configure_step import ConfigureStep
from .detect_step import DetectStep
from .gpu_stage import GpuStage
from .install_deps_step import InstallDepsStep
from .machine_actions import MachineActions
from .packages import refresh_windows_path
from .uninstall_step import UninstallStep

warnings.warn(
    "sushicore.provision.steps is deprecated; import DetectStep, InstallDepsStep, ConfigureStep, "
    "UninstallStep, GpuStage and MachineActions from the module named after each, "
    "and refresh_windows_path from sushicore.provision.packages",
    DeprecationWarning, stacklevel=2)

__all__ = [
    "ConfigureStep",
    "DetectStep",
    "GpuStage",
    "InstallDepsStep",
    "MachineActions",
    "UninstallStep",
    "refresh_windows_path",
]
