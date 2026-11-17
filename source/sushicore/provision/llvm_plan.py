# llvm_plan.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The contract for how one target supplies the LLVM AdaptiveCpp builds against, and the registry of its plans."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence, final

from .packages import IPackageManager, LinuxPackageManager
from .target_plans import TargetPlans


@final
@dataclass(frozen=True, slots=True)
class LlvmRequest:
    """What a plan may use to supply the LLVM dependency of the acpp build.

    Args:
        mgr: The Linux distro package manager, or None when unavailable.
        vcpkg: The vcpkg manager, or None when unavailable.
        winget: The winget manager, or None when unavailable.
        assume_yes: Skip the consent prompt for the heavy LLVM download.
        llvm_bases: The Windows LLVM install roots to look in; the defaults when ``None``.
    """

    mgr: LinuxPackageManager | None
    vcpkg: IPackageManager | None
    winget: IPackageManager | None
    assume_yes: bool
    llvm_bases: Sequence[Path] | None
    console: Any


class ILlvmPlan(ABC):
    """Installs and locates the LLVM development files one target builds acpp against."""

    @abstractmethod
    def resolve(self, request: LlvmRequest) -> tuple[str | None, str | None]:
        """Install what the build needs and return ``(LLVM_DIR, clang_prefix)``, or ``(None, None)``."""


#: The LLVM plan of each target, or its factory, registered by the modules of ``llvm_plans``.
LLVM_PLANS: TargetPlans[ILlvmPlan] = TargetPlans("sushicore.provision.llvm_plans")
