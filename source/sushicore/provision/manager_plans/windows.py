# windows.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The manager plan of the Windows target."""

from __future__ import annotations

from typing import Any, final

from ..config import ProvisionConfig
from ..dependency_home import DEFAULT_HOME, DependencyHome
from ..download_checking import DownloadChecking
from ..licence_consent import LicenceConsent
from ..manager_plan import MANAGER_PLANS, IManagerPlan
from ..packages import DirectDownloadWindowsManager, IPackageManager, VcpkgManager, WingetManager
from ..target import K_WINDOWS


@final
class WindowsManagerPlan(IManagerPlan):
    """Provisions through winget, the direct downloads and vcpkg."""

    def __init__(self, *, home: DependencyHome = DEFAULT_HOME,
                 verifier: DownloadChecking | None = None) -> None:
        """Bind the home and the download verifier the managers it builds read.

        Args:
            home: The home whose root the managers use; the deprecated default home when omitted.
            verifier: Checks the direct downloads; the deprecated default slot's when ``None``.
        """
        self._home = home
        self._verifier = verifier

    def managers(self, cfg: ProvisionConfig, consent: LicenceConsent | None,
                 console: Any) -> list[IPackageManager]:
        """Return winget, the direct downloads and vcpkg."""
        return [WingetManager(consent, console=console),
                DirectDownloadWindowsManager(console=console, home=self._home,
                                           verifier=self._verifier),
                VcpkgManager(cfg, console=console, home=self._home)]


MANAGER_PLANS.register_factory(K_WINDOWS, WindowsManagerPlan)
