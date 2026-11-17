# toolchain_install.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Installs the SYCL toolchains a run selected, for every target."""

from __future__ import annotations

from .dependency_presence import named_manager
from .install_deps_plan import InstallServices
from .packages import IPackageManager
from .pipeline import InstallContext
from .toolchains import adaptivecpp, intel_llvm


def install_toolchains(ctx: InstallContext, services: InstallServices,
                       mgr: IPackageManager | None, vcpkg: IPackageManager | None) -> None:
    """Install the SYCL toolchains this run selected, recording their resolved paths."""
    if ctx.selection.install_intel_llvm:
        llvm = intel_llvm.install_intel_llvm(
            ctx.cfg, ctx.dry_run, refresh=ctx.refresh_toolchains,
            refresh_command=ctx.refresh_command)
        if llvm:
            ctx.resolved_paths["llvm_root"] = llvm
        else:
            services.console.warn("intel/llvm bundle not installed; the intel-llvm "
                                  "toolchain will be unavailable.")

    if ctx.selection.install_acpp:
        acpp = adaptivecpp.install_adaptivecpp(
            ctx.cfg, mgr, vcpkg, ctx.dry_run,
            assume_yes=ctx.assume_acpp_llvm,
            winget=named_manager(services.managers, "winget"))
        if acpp:
            ctx.resolved_paths["acpp_exe"] = acpp
        elif not ctx.selection.install_intel_llvm:
            message = ("AdaptiveCpp is the only toolchain selected but it did "
                       "not install; the project will not build.")
            services.console.warn(f"{message} {ctx.fallback_hint}".strip())
