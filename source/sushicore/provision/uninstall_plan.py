# uninstall_plan.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The contract for what removing a run's packages does on one target, and the registry of its plans."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, final

from .fragments import IDependencySource
from .packages import IPackageManager
from .install_context import InstallContext
from .target_plans import TargetPlans


@final
@dataclass(frozen=True, slots=True)
class UninstallServices:
    """What the uninstall step hands a plan: the run's source, managers and console.

    Args:
        source: The dependency source the manifests declare.
        managers: The package managers this run installed through.
        console: The console the plan prints through.
    """

    source: IDependencySource
    managers: list[IPackageManager]
    console: Any


class IUninstallPlan(ABC):
    """Removes the packages and portable tools one target's install placed."""

    @abstractmethod
    def remove_packages(self, ctx: InstallContext, services: UninstallServices) -> None:
        """Remove the manifest packages, vcpkg ports and portable tools of the target."""


#: The uninstall plan of each target, registered by the modules of ``uninstall_plans``.
UNINSTALL_PLANS: TargetPlans[IUninstallPlan] = TargetPlans("sushicore.provision.uninstall_plans")
