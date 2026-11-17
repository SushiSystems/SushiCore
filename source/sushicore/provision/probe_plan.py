# probe_plan.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The contract for what tool probing finds on one target, and the registry of its plans."""

from __future__ import annotations

from abc import ABC, abstractmethod

from .config import ProvisionConfig
from .target_plans import TargetPlans


class IProbePlan(ABC):
    """Finds the SYCL compiler and the machine-specific tool paths of one target."""

    @abstractmethod
    def find_sycl_compiler(self, cfg: ProvisionConfig) -> tuple[str | None, str]:
        """Return ``(compiler, location)`` of the working SYCL compiler, or ``(None, "")``."""

    @abstractmethod
    def resolve_local_config(self, cfg: ProvisionConfig) -> dict[str, str]:
        """Return the tool paths found on this machine, only the ones actually found."""


#: The probe plan of each target, registered by the modules of ``probe_plans``.
PROBE_PLANS: TargetPlans[IProbePlan] = TargetPlans("sushicore.provision.probe_plans")
