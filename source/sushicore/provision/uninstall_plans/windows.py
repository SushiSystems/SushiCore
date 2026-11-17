# windows.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The uninstall plan of the Windows target."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import final

from ..dependency_presence import named_manager
from ..package_lists import dedup
from ..packages import tools_dir
from ..install_context import InstallContext
from ..target import K_WINDOWS
from ..uninstall_plan import UNINSTALL_PLANS, IUninstallPlan, UninstallServices


@final
class WindowsUninstallPlan(IUninstallPlan):
    """Removes the vcpkg ports of the manifest and the portable ninja, cmake and doxygen."""

    def remove_packages(self, ctx: InstallContext, services: UninstallServices) -> None:
        """Remove Windows vcpkg ports and portable tools."""
        console = services.console
        vcpkg = named_manager(services.managers, "vcpkg")

        ports: list[str] = []
        for dep in services.source.selected("windows", ctx.gpu):
            ports.extend(dep.windows_vcpkg)
        ports = dedup(ports)

        if vcpkg and ports:
            console.info(f"Removing vcpkg ports: {', '.join(ports)}")
            vcpkg.remove(ports, ctx.dry_run)

        tools = tools_dir(home=ctx.home)
        ninja_exe = tools / "ninja.exe"
        if ninja_exe.is_file():
            if ctx.dry_run:
                console.info(f"(dry-run) would remove {ninja_exe}")
            else:
                ninja_exe.unlink()
                console.info(f"Removed {ninja_exe}")
        self._remove_tree(tools / "cmake", ctx, services)
        self._remove_tree(tools / "doxygen", ctx, services)
        if tools.is_dir() and not any(tools.iterdir()) and not ctx.dry_run:
            tools.rmdir()

    @staticmethod
    def _remove_tree(folder: Path, ctx: InstallContext, services: UninstallServices) -> None:
        """Remove *folder* when it exists, or say it would be removed on a dry run."""
        if not folder.is_dir():
            return
        if ctx.dry_run:
            services.console.info(f"(dry-run) would remove {folder}")
        else:
            shutil.rmtree(folder, ignore_errors=True)
            services.console.info(f"Removed {folder}")


UNINSTALL_PLANS.register(K_WINDOWS, WindowsUninstallPlan())
