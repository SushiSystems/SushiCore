# linux.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The uninstall plan of the Linux target."""

from __future__ import annotations

from typing import final

from ..dependency_presence import available_linux_manager, named_manager
from ..package_lists import dedup
from ..install_context import InstallContext
from ..target import K_LINUX
from ..uninstall_plan import UNINSTALL_PLANS, IUninstallPlan, UninstallServices


@final
class LinuxUninstallPlan(IUninstallPlan):
    """Removes the distro packages and the vcpkg ports of the manifest."""

    def remove_packages(self, ctx: InstallContext, services: UninstallServices) -> None:
        """Remove Linux packages and vcpkg ports."""
        mgr = available_linux_manager(services.managers)
        vcpkg = named_manager(services.managers, "vcpkg")
        pkgs: list[str] = []
        vcpkg_ports: list[str] = []
        for dep in services.source.selected("linux", ctx.gpu):
            pkgs.extend(mgr.translate_apt(dep.linux_apt) if mgr else dep.linux_apt)
            vcpkg_ports.extend(dep.vcpkg_fallback_ports("linux"))
        pkgs = dedup(pkgs)
        vcpkg_ports = dedup(vcpkg_ports)

        if mgr and pkgs:
            services.console.info(f"Removing via {mgr.name}: {', '.join(pkgs)}")
            mgr.remove(pkgs, ctx.dry_run)

        if vcpkg and vcpkg_ports:
            services.console.info(f"Removing vcpkg ports: {', '.join(vcpkg_ports)}")
            vcpkg.remove(vcpkg_ports, ctx.dry_run)


UNINSTALL_PLANS.register(K_LINUX, LinuxUninstallPlan())
