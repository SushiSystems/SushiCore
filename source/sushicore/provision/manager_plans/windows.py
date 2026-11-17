# windows.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The manager plan of the Windows target."""

from __future__ import annotations

from typing import final

from ..config import ProvisionConfig
from ..licence_consent import LicenceConsent
from ..manager_plan import MANAGER_PLANS, IManagerPlan
from ..packages import DirectDownloadWindowsManager, IPackageManager, VcpkgManager, WingetManager
from ..target import K_WINDOWS


@final
class WindowsManagerPlan(IManagerPlan):
    """Provisions through winget, the direct downloads and vcpkg."""

    def managers(self, cfg: ProvisionConfig, consent: LicenceConsent | None) -> list[IPackageManager]:
        """Return winget, the direct downloads and vcpkg."""
        return [WingetManager(consent), DirectDownloadWindowsManager(), VcpkgManager(cfg)]


MANAGER_PLANS.register(K_WINDOWS, WindowsManagerPlan())
