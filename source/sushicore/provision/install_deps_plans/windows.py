# windows.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The install plan of the Windows target."""

from __future__ import annotations

from typing import final

from ..dependency_presence import dep_installed, named_manager
from ..install_deps_plan import INSTALL_PLANS, IInstallPlan, InstallServices
from ..licence_consent import Licence, is_accepted
from ..llvm_plans.windows import llvm_missing
from ..package_lists import dedup
from ..packages import WINGET_ID_TO_CMD, IPackageManager
from ..packages.winget_licence import IWingetLicences
from ..install_context import InstallContext
from ..step_result import StepResult
from ..target import K_WINDOWS
from ..toolchain_install import install_toolchains, toolchain_licences

#: The winget id of the Visual Studio 2022 Build Tools.
K_VS_BUILD_TOOLS_ID = "Microsoft.VisualStudio.2022.BuildTools"

#: The winget id of the LLVM release AdaptiveCpp builds against.
K_LLVM_ID = "LLVM.LLVM"


@final
class WindowsInstallPlan(IInstallPlan):
    """Installs portable tools, git, vcpkg ports and Visual Studio Build Tools through winget."""

    def licences(self, ctx: InstallContext, needed: list[Licence],
                 services: InstallServices) -> list[Licence]:
        """Return *needed* plus the licences of the winget packages this run installs."""
        winget = named_manager(services.managers, "winget")
        if winget and winget.available():
            git_missing = not services.actions.which("git")
            vs_missing = self._vs_build_tools_missing(services, winget)
            llvm_wanted = (ctx.selection.install_acpp and ctx.assume_acpp_llvm
                           and llvm_missing())
            wanted = [(git_missing, "Git.Git"), (vs_missing, K_VS_BUILD_TOOLS_ID),
                      (llvm_wanted, K_LLVM_ID)]
            needed.extend(held for held in (self._licence_of(winget, pkg)
                                            for missing, pkg in wanted if missing)
                          if held is not None)
        return needed + toolchain_licences(ctx)

    def run(self, ctx: InstallContext, services: InstallServices) -> StepResult:
        """Install dependencies, the toolchains and the GPU stack on Windows."""
        services.actions.refresh_path()
        winget = named_manager(services.managers, "winget")
        direct = named_manager(services.managers, "direct-download")
        vcpkg = named_manager(services.managers, "vcpkg")

        tool_ok = self._install_portable_tools(ctx, services, direct)
        tool_ok = self._install_git(ctx, services, winget, direct) and tool_ok

        _ports, lib_ok = self._install_vcpkg_ports(ctx, services, vcpkg)
        if lib_ok is None:  # vcpkg required but missing
            return StepResult.FAILED

        tool_ok = self._install_vs_build_tools(ctx, services, winget) and tool_ok

        tool_ok = install_toolchains(ctx, services, mgr=None, vcpkg=vcpkg) and tool_ok

        services.gpu.provision_windows(ctx)

        return StepResult.OK if (tool_ok and lib_ok) else StepResult.FAILED

    def _install_portable_tools(self, ctx: InstallContext, services: InstallServices,
                                direct: IPackageManager | None) -> bool:
        """Install cmake, ninja and doxygen portably into the deps folder."""
        portable = ["Kitware.CMake", "Ninja-build.Ninja", "DimitriVanHeesch.Doxygen"]
        missing = [pkg for pkg in portable
                   if not services.actions.which(WINGET_ID_TO_CMD.get(pkg, ""))]
        if missing and direct:
            services.console.info(
                "Installing CMake, Ninja, and Doxygen portably into the deps folder ...")
            return direct.install(missing, ctx.dry_run)
        if not missing:
            services.console.info("cmake + ninja + doxygen already present, skipping.")
        return True

    def _install_git(self, ctx: InstallContext, services: InstallServices,
                     winget: IPackageManager | None, direct: IPackageManager | None) -> bool:
        """Install git through winget, or direct-download, when it is missing."""
        if services.actions.which("git"):
            return True
        if winget and winget.available():
            services.console.info("Installing git via winget ...")
            return winget.install(["Git.Git"], ctx.dry_run)
        if direct:
            return direct.install(["Git.Git"], ctx.dry_run)
        services.console.warn("git not found and no installer available; install it manually.")
        return True

    def _install_vcpkg_ports(self, ctx: InstallContext, services: InstallServices,
                             vcpkg: IPackageManager | None) -> tuple[list[str], bool | None]:
        """Install the manifest's C++ library ports via vcpkg.

        Returns:
            The ports and whether the install succeeded; ``None`` when ports
            were needed but vcpkg itself is missing.
        """
        ports: list[str] = []
        for dep in services.source.selected("windows", ctx.gpu):
            if vcpkg and dep_installed(dep, vcpkg, "windows"):
                services.console.info(f"{dep.name}: already installed, skipping.")
                continue
            ports.extend(dep.windows_vcpkg)
        ports = dedup(ports)

        if not ports:
            return ports, True
        if vcpkg is None:
            services.console.error("vcpkg manager missing; cannot install C++ libs.")
            return ports, None
        services.console.info(f"Installing via vcpkg: {', '.join(ports)}")
        ok = vcpkg.install(ports, ctx.dry_run)
        ctx.installed.extend(ports)
        return ports, ok

    def _install_vs_build_tools(self, ctx: InstallContext, services: InstallServices,
                                winget: IPackageManager | None) -> bool:
        """Install the Visual Studio 2022 Build Tools (C++ workload) through winget.

        Any Visual Studio edition whose C++ tools vcvars64.bat is found already supplies the
        host compiler, so nothing is installed then.
        """
        console = services.console
        if not (winget and winget.available()):
            return True
        if not self._vs_build_tools_missing(services, winget):
            return True
        if ctx.dry_run:
            console.info("(dry-run) skipping VS Build Tools install.")
            return True
        licence = self._licence_of(winget, K_VS_BUILD_TOOLS_ID)
        if licence is None or not is_accepted(ctx.consent, licence):
            console.error("Visual Studio Build Tools need consent to their licence"
                          + (f": {licence.link}" if licence else "."))
            return False

        vs_cmd = [
            "winget", "install",
            "--id", K_VS_BUILD_TOOLS_ID, "-e",
            "--accept-package-agreements", "--accept-source-agreements",
            "--override",
            "--add Microsoft.VisualStudio.Workload.VCTools "
            "--includeRecommended --quiet --wait --norestart",
        ]
        with console.console.status(
            "[header]Installing Visual Studio Build Tools "
            "(C++ workloads) — this may take 10–20 minutes.",
            spinner="bouncingBar",
        ):
            rc = services.actions.run_command(vs_cmd, console)
        if rc != 0:
            console.warn("Visual Studio Build Tools install failed or was cancelled.")
            return False
        console.success("Visual Studio Build Tools installed.")
        return True

    @staticmethod
    def _licence_of(winget: IPackageManager, pkg: str) -> Licence | None:
        """Returns the licence *winget* names for *pkg*; None when it names none."""
        return winget.licence_of(pkg) if isinstance(winget, IWingetLicences) else None

    @staticmethod
    def _vs_build_tools_missing(services: InstallServices, winget: IPackageManager) -> bool:
        """Report whether no Visual Studio C++ toolset is found and winget lists no Build Tools."""
        if services.actions.find_vcvars() is not None:
            return False
        return not winget.is_installed(K_VS_BUILD_TOOLS_ID)


INSTALL_PLANS.register(K_WINDOWS, WindowsInstallPlan())
