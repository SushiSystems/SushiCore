# linux.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The manager plan of the Linux target."""

from __future__ import annotations

from typing import final

from ..config import ProvisionConfig
from ..licence_consent import LicenceConsent
from ..manager_plan import MANAGER_PLANS, IManagerPlan
from ..packages import (
    AptManager,
    DnfManager,
    IPackageManager,
    PacmanManager,
    VcpkgManager,
    YumManager,
    ZypperManager,
)
from ..target import K_LINUX


@final
class LinuxManagerPlan(IManagerPlan):
    """Provisions through the distro managers and vcpkg."""

    def managers(self, cfg: ProvisionConfig, consent: LicenceConsent | None) -> list[IPackageManager]:
        """Return the distro managers and vcpkg."""
        return [AptManager(), DnfManager(), YumManager(), PacmanManager(), ZypperManager(),
                VcpkgManager(cfg)]


MANAGER_PLANS.register(K_LINUX, LinuxManagerPlan())
