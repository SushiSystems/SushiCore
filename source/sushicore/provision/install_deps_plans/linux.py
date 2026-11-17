# linux.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The install plan of the Linux target."""

from __future__ import annotations

from typing import final

from ..dependency_presence import available_linux_manager, dep_installed, named_manager
from ..install_deps_plan import INSTALL_PLANS, IInstallPlan, InstallServices
from ..licence_consent import Licence
from ..package_lists import dedup
from ..pipeline import InstallContext, StepResult
from ..target import K_LINUX
from ..toolchain_install import install_toolchains

#: System toolchain installed through the toolchain manager, not the manifest.
K_LINUX_TOOLCHAIN_APT = ["build-essential", "cmake", "ninja-build", "git"]


@final
class LinuxInstallPlan(IInstallPlan):
    """Installs through the distro package manager, with vcpkg for what no distro package covers."""

    def licences(self, ctx: InstallContext, needed: list[Licence],
                 services: InstallServices) -> list[Licence]:
        """Return *needed* as it is: Linux installs through distro packages with no licence prompt."""
        return needed

    def run(self, ctx: InstallContext, services: InstallServices) -> StepResult:
        """Install dependencies, the toolchains and the GPU stack on Linux."""
        console = services.console
        mgr = available_linux_manager(services.managers)
        if mgr is None:
            msg = ("No supported package manager found (apt, dnf, yum, pacman, zypper). "
                   "Install python3, pip, git, cmake, and ninja manually, then re-run.")
            if ctx.dry_run:
                console.warn(f"(dry-run) {msg}")
                return StepResult.SKIPPED
            console.error(msg)
            return StepResult.FAILED

        console.info(f"Using package manager: {mgr.name}")
        vcpkg = named_manager(services.managers, "vcpkg")

        # Translate the generic apt toolchain list to native package names.
        pkgs: list[str] = list(mgr.translate_apt(K_LINUX_TOOLCHAIN_APT))
        vcpkg_ports: list[str] = []
        for dep in services.source.selected("linux", ctx.gpu):
            if dep_installed(dep, mgr, "linux", vcpkg):
                console.info(f"{dep.name}: already installed, skipping.")
                continue
            if dep.linux_apt:
                pkgs.extend(mgr.translate_apt(dep.linux_apt))
            else:
                vcpkg_ports.extend(dep.vcpkg_fallback_ports("linux"))

        pkgs = dedup(pkgs)
        vcpkg_ports = dedup(vcpkg_ports)

        ok = True
        if pkgs:
            console.info(f"Installing via {mgr.name}: {', '.join(pkgs)}")
            ok = mgr.install(pkgs, ctx.dry_run)
            ctx.installed.extend(pkgs)
        else:
            console.info("No apt packages to install.")

        if vcpkg_ports:
            if vcpkg is None:
                console.warn(f"No vcpkg manager available; cannot install "
                             f"{', '.join(vcpkg_ports)} (no apt package exists for "
                             f"these on Linux). Install them manually.")
                ok = False
            else:
                console.info(f"Installing via vcpkg: {', '.join(vcpkg_ports)}")
                ok = vcpkg.install(vcpkg_ports, ctx.dry_run) and ok
                ctx.installed.extend(vcpkg_ports)

        if not pkgs and not vcpkg_ports:
            console.info("All packages already present.")

        ok = install_toolchains(ctx, services, mgr=mgr, vcpkg=None) and ok

        services.gpu.provision_linux(ctx, mgr)
        return StepResult.OK if ok else StepResult.FAILED


INSTALL_PLANS.register(K_LINUX, LinuxInstallPlan())
