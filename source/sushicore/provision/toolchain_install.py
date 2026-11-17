# toolchain_install.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Installs the SYCL toolchains a run selected, for every target."""

from __future__ import annotations

from .install_deps_plan import InstallServices
from .licence_consent import Licence
from .packages import IPackageManager, LinuxPackageManager
from .install_context import InstallContext
from .toolchains.registry import DEFAULT_REGISTRY, ToolchainRegistry
from .toolchains.toolchain import ToolchainEnv


def install_toolchains(ctx: InstallContext, services: InstallServices,
                       mgr: LinuxPackageManager | None, vcpkg: IPackageManager | None,
                       registry: ToolchainRegistry = DEFAULT_REGISTRY) -> bool:
    """Install each registered toolchain the run selected, in registry order.

    Args:
        mgr: The Linux distro package manager; None on a target without one.
        vcpkg: The vcpkg manager, or None when unavailable.
        registry: The toolchains to walk; the declared set when omitted.

    Returns:
        False when a selected toolchain reported a fatal failure.
    """
    env = ToolchainEnv(console=services.console, managers=services.managers, mgr=mgr,
                       vcpkg=vcpkg,
                       install_oneapi=lambda run: services.actions.install_oneapi(
                           run, services.console))
    selected = ctx.selection.as_dict()
    ok = True
    for toolchain in registry.all():
        if selected.get(toolchain.selection_field, False):
            ok = toolchain.install(ctx, env) and ok
    return ok


def toolchain_licences(ctx: InstallContext,
                       registry: ToolchainRegistry = DEFAULT_REGISTRY) -> list[Licence]:
    """Return the licences the registered toolchains need for *ctx*, in registry order."""
    return [licence for toolchain in registry.all() for licence in toolchain.licences(ctx)]
