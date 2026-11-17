# install_deps_plan.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The contract for what installing dependencies does on one target, and the registry of its plans."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, final

from .fragments import IDependencySource
from .gpu_stage import GpuStage
from .licence_consent import Licence
from .machine_actions import MachineActions
from .packages import IPackageManager
from .install_context import InstallContext
from .step_result import StepResult
from .target_plans import TargetPlans


@final
@dataclass(frozen=True, slots=True)
class InstallServices:
    """What the install step hands a plan: the run's source, managers, console and machine.

    Args:
        source: The dependency source the manifests declare.
        managers: The package managers this run installs through.
        console: The console the plan prints through.
        actions: The machine calls.
        gpu: The GPU part of the run.
    """

    source: IDependencySource
    managers: list[IPackageManager]
    console: Any
    actions: MachineActions
    gpu: GpuStage


class IInstallPlan(ABC):
    """Names the licences one target's installers need and installs on that target."""

    @abstractmethod
    def licences(self, ctx: InstallContext, needed: list[Licence],
                 services: InstallServices) -> list[Licence]:
        """Return *needed* plus the licences of the packages this run installs on the target."""

    @abstractmethod
    def run(self, ctx: InstallContext, services: InstallServices) -> StepResult:
        """Install the dependencies, the toolchains and the GPU stack on the target."""


#: The install plan of each target, registered by the modules of ``install_deps_plans``.
INSTALL_PLANS: TargetPlans[IInstallPlan] = TargetPlans("sushicore.provision.install_deps_plans")
