# linux.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The LLVM plan of the Linux target."""

from __future__ import annotations

from typing import final

from ..llvm_plan import LLVM_PLANS, ILlvmPlan, LlvmRequest
from ..target import K_LINUX
from ..toolchains.adaptivecpp import ACPP_LLVM


@final
class LinuxLlvmPlan(ILlvmPlan):
    """Installs the acpp build dependencies through the distro package manager."""

    def resolve(self, request: LlvmRequest) -> tuple[str | None, str | None]:
        """Install acpp build deps via the distro manager; return ``(LLVM_DIR, clang_prefix)``."""
        if request.mgr is None:
            return (None, None)
        return request.mgr.install_acpp_build_deps(ACPP_LLVM)


LLVM_PLANS.register(K_LINUX, LinuxLlvmPlan())
