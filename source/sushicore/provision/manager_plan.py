# manager_plan.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The contract for the package managers one target provisions through, and the registry of its plans."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .config import ProvisionConfig
from .licence_consent import LicenceConsent
from .packages import IPackageManager
from .target_plans import TargetPlans


class IManagerPlan(ABC):
    """Builds the package managers one target provisions its dependencies through."""

    @abstractmethod
    def managers(self, cfg: ProvisionConfig, consent: LicenceConsent | None,
                 console: Any) -> list[IPackageManager]:
        """Return the managers, in the order they are tried; *consent* gates winget's installs.

        Each manager prints through *console*.
        """


#: The manager plan factory of each target, registered by the modules of ``manager_plans``.
MANAGER_PLANS: TargetPlans[IManagerPlan] = TargetPlans("sushicore.provision.manager_plans")
