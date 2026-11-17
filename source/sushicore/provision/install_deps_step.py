# install_deps_step.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Installs the missing manifest dependencies and the system toolchain."""

from __future__ import annotations

from typing import Any

from ._output import console
from .dependency_presence import available_linux_manager, dep_installed, named_manager
from .download_verifier import DownloadVerifier, bind_verifier
from .fragments import IDependencySource
from .packages import (
    IPackageManager,
    WINGET_ID_TO_CMD,
)
from .package_lists import dedup
from .packages.winget_licence import IWingetLicences
from .pipeline import InstallContext, Step, StepResult
from .gpu_stage import GpuStage
from .licence_consent import Licence, is_accepted
from .machine_actions import MachineActions
from .toolchains import adaptivecpp, intel_llvm
from .target import K_LINUX, K_WINDOWS, target_of
from .toolchains.oneapi import oneapi_licences

#: System toolchain installed through the toolchain manager, not the manifest.
_LINUX_TOOLCHAIN_APT = ["build-essential", "cmake", "ninja-build", "git"]

#: The winget id of the Visual Studio 2022 Build Tools.
_VS_BUILD_TOOLS_ID = "Microsoft.VisualStudio.2022.BuildTools"

#: The winget id of the LLVM release AdaptiveCpp builds against.
_LLVM_ID = "LLVM.LLVM"


class InstallDepsStep(Step):
    """Install missing manifest dependencies and system toolchain."""

    name = "install-deps"

    def __init__(self, source: IDependencySource, managers: list[IPackageManager],
                 *, console: Any = console, actions: MachineActions | None = None,
                 gpu: GpuStage | None = None) -> None:
        """Wire the dependency source, the package managers and the machine.

        Args:
            console: The console the step prints through.
            actions: The machine calls; the real ones when omitted.
            gpu: The GPU part of the run; built from *console* and *actions* when omitted.
        """
        self._source = source
        self._managers = managers
        self._console = console
        self._actions = actions or MachineActions()
        self._gpu = gpu or GpuStage(console=console, actions=self._actions)
        self._licence_plans = {K_WINDOWS: self._windows_licences, K_LINUX: self._linux_licences}
        self._run_plans = {K_WINDOWS: self._run_windows, K_LINUX: self._run_linux}

    def licences(self, ctx: InstallContext) -> list[Licence]:
        """Returns the third-party licences this step's installers need for *ctx*.

        Read after detection, so *ctx* already holds what the machine has.
        """
        needed: list[Licence] = self._gpu.toolkit_licences(ctx)
        return self._licence_plans[target_of(ctx.cfg).name](ctx, needed)

    def _linux_licences(self, ctx: InstallContext, needed: list[Licence]) -> list[Licence]:
        """Return *needed* as it is: Linux installs through distro packages with no licence prompt."""
        return needed

    def _windows_licences(self, ctx: InstallContext, needed: list[Licence]) -> list[Licence]:
        """Return *needed* plus the licences of the winget packages this run installs."""
        winget = named_manager(self._managers, "winget")
        if winget and winget.available():
            git_missing = not self._actions.which("git")
            vs_missing = self._vs_build_tools_missing(winget)
            llvm_wanted = (ctx.selection.install_acpp and ctx.assume_acpp_llvm
                           and adaptivecpp.llvm_missing())
            wanted = [(git_missing, "Git.Git"), (vs_missing, _VS_BUILD_TOOLS_ID),
                      (llvm_wanted, _LLVM_ID)]
            needed.extend(held for held in (self._licence_of(winget, pkg)
                                            for missing, pkg in wanted if missing)
                          if held is not None)
        return needed + oneapi_licences(ctx)

    def run(self, ctx: InstallContext) -> StepResult:
        """Run the install routine of this platform with the fragments' digests bound.

        Raises:
            DigestMismatchError: A download's SHA-256 is not the one its entry pins.
        """
        platform = ctx.cfg.platform
        bind_verifier(DownloadVerifier(self._source.digests(platform),
                                       self._source.downloads(platform)))
        try:
            return self._run_plans[target_of(ctx.cfg).name](ctx)
        finally:
            bind_verifier(None)

    def _install_toolchains(self, ctx: InstallContext,
                            mgr: IPackageManager | None,
                            vcpkg: IPackageManager | None) -> None:
        """Install the SYCL toolchains this run selected, recording their resolved paths."""
        if ctx.selection.install_intel_llvm:
            llvm = intel_llvm.install_intel_llvm(
                ctx.cfg, ctx.dry_run, refresh=ctx.refresh_toolchains,
                refresh_command=ctx.refresh_command)
            if llvm:
                ctx.resolved_paths["llvm_root"] = llvm
            else:
                self._console.warn("intel/llvm bundle not installed; the intel-llvm "
                             "toolchain will be unavailable.")

        if ctx.selection.install_acpp:
            acpp = adaptivecpp.install_adaptivecpp(
                ctx.cfg, mgr, vcpkg, ctx.dry_run,
                assume_yes=ctx.assume_acpp_llvm,
                winget=named_manager(self._managers, "winget"))
            if acpp:
                ctx.resolved_paths["acpp_exe"] = acpp
            elif not ctx.selection.install_intel_llvm:
                message = ("AdaptiveCpp is the only toolchain selected but it did "
                           "not install; the project will not build.")
                self._console.warn(f"{message} {ctx.fallback_hint}".strip())

    def _run_linux(self, ctx: InstallContext) -> StepResult:
        """Install dependencies, the toolchains and the GPU stack on Linux."""
        mgr = available_linux_manager(self._managers)
        if mgr is None:
            msg = ("No supported package manager found (apt, dnf, yum, pacman, zypper). "
                   "Install python3, pip, git, cmake, and ninja manually, then re-run.")
            if ctx.dry_run:
                self._console.warn(f"(dry-run) {msg}")
                return StepResult.SKIPPED
            self._console.error(msg)
            return StepResult.FAILED

        self._console.info(f"Using package manager: {mgr.name}")
        vcpkg = named_manager(self._managers, "vcpkg")

        # Translate the generic apt toolchain list to native package names.
        pkgs: list[str] = list(mgr.translate_apt(_LINUX_TOOLCHAIN_APT))
        vcpkg_ports: list[str] = []
        for dep in self._source.selected("linux", ctx.gpu):
            if dep_installed(dep, mgr, "linux", vcpkg):
                self._console.info(f"{dep.name}: already installed, skipping.")
                continue
            if dep.linux_apt:
                pkgs.extend(mgr.translate_apt(dep.linux_apt))
            else:
                vcpkg_ports.extend(dep.vcpkg_fallback_ports("linux"))

        pkgs = dedup(pkgs)
        vcpkg_ports = dedup(vcpkg_ports)

        ok = True
        if pkgs:
            self._console.info(f"Installing via {mgr.name}: {', '.join(pkgs)}")
            ok = mgr.install(pkgs, ctx.dry_run)
            ctx.installed.extend(pkgs)
        else:
            self._console.info("No apt packages to install.")

        if vcpkg_ports:
            if vcpkg is None:
                self._console.warn(f"No vcpkg manager available; cannot install "
                             f"{', '.join(vcpkg_ports)} (no apt package exists for "
                             f"these on Linux). Install them manually.")
                ok = False
            else:
                self._console.info(f"Installing via vcpkg: {', '.join(vcpkg_ports)}")
                ok = vcpkg.install(vcpkg_ports, ctx.dry_run) and ok
                ctx.installed.extend(vcpkg_ports)

        if not pkgs and not vcpkg_ports:
            self._console.info("All packages already present.")

        self._install_toolchains(ctx, mgr=mgr, vcpkg=None)

        if ctx.selection.oneapi and mgr.automates_oneapi:
            self._console.info("oneAPI: configuring the Intel apt repository and installing "
                         "intel-oneapi-compiler-dpcpp-cpp.")
            if not mgr.install_oneapi(ctx.dry_run):
                self._console.warn("oneAPI compiler install failed; continuing "
                             "(intel-llvm/AdaptiveCpp remain available).")
        elif ctx.selection.oneapi:
            self._console.warn(f"oneAPI on {mgr.name} is not automated; install the "
                         "Intel oneAPI DPC++ compiler manually.")

        self._gpu.provision_linux(ctx, mgr)
        return StepResult.OK if ok else StepResult.FAILED

    def _run_windows(self, ctx: InstallContext) -> StepResult:
        """Install dependencies, the toolchains and the GPU stack on Windows."""
        self._actions.refresh_path()
        winget = named_manager(self._managers, "winget")
        direct = named_manager(self._managers, "direct-download")
        vcpkg  = named_manager(self._managers, "vcpkg")

        tool_ok = self._install_portable_tools(ctx, direct)
        tool_ok = self._install_git(ctx, winget, direct) and tool_ok

        ports, lib_ok = self._install_vcpkg_ports(ctx, vcpkg)
        if lib_ok is None:  # vcpkg required but missing
            return StepResult.FAILED

        tool_ok = self._install_vs_build_tools(ctx, winget) and tool_ok

        self._install_toolchains(ctx, mgr=None, vcpkg=vcpkg)

        self._gpu.provision_windows(ctx)

        tool_ok = self._actions.install_oneapi(ctx) and tool_ok

        return StepResult.OK if (tool_ok and lib_ok) else StepResult.FAILED

    def _install_portable_tools(self, ctx: InstallContext,
                                direct: IPackageManager | None) -> bool:
        """Install cmake, ninja and doxygen portably into the deps folder."""
        portable = ["Kitware.CMake", "Ninja-build.Ninja", "DimitriVanHeesch.Doxygen"]
        missing = [pkg for pkg in portable if not self._actions.which(WINGET_ID_TO_CMD.get(pkg, ""))]
        if missing and direct:
            self._console.info("Installing CMake, Ninja, and Doxygen portably into the deps folder ...")
            return direct.install(missing, ctx.dry_run)
        if not missing:
            self._console.info("cmake + ninja + doxygen already present, skipping.")
        return True

    def _install_git(self, ctx: InstallContext, winget: IPackageManager | None,
                     direct: IPackageManager | None) -> bool:
        """Install git through winget, or direct-download, when it is missing."""
        if self._actions.which("git"):
            return True
        if winget and winget.available():
            self._console.info("Installing git via winget ...")
            return winget.install(["Git.Git"], ctx.dry_run)
        if direct:
            return direct.install(["Git.Git"], ctx.dry_run)
        self._console.warn("git not found and no installer available; install it manually.")
        return True

    def _install_vcpkg_ports(self, ctx: InstallContext,
                             vcpkg: IPackageManager | None) -> tuple[list[str], bool | None]:
        """Install the manifest's C++ library ports via vcpkg.

        Returns:
            The ports and whether the install succeeded; ``None`` when ports
            were needed but vcpkg itself is missing.
        """
        ports: list[str] = []
        for dep in self._source.selected("windows", ctx.gpu):
            if vcpkg and dep_installed(dep, vcpkg, "windows"):
                self._console.info(f"{dep.name}: already installed, skipping.")
                continue
            ports.extend(dep.windows_vcpkg)
        ports = dedup(ports)

        if not ports:
            return ports, True
        if vcpkg is None:
            self._console.error("vcpkg manager missing; cannot install C++ libs.")
            return ports, None
        self._console.info(f"Installing via vcpkg: {', '.join(ports)}")
        ok = vcpkg.install(ports, ctx.dry_run)
        ctx.installed.extend(ports)
        return ports, ok

    def _install_vs_build_tools(self, ctx: InstallContext,
                                winget: IPackageManager | None) -> bool:
        """Install the Visual Studio 2022 Build Tools (C++ workload) through winget.

        Any Visual Studio edition whose C++ tools vcvars64.bat is found already supplies the
        host compiler, so nothing is installed then.
        """
        if not (winget and winget.available()):
            return True
        if not self._vs_build_tools_missing(winget):
            return True
        if ctx.dry_run:
            self._console.info("(dry-run) skipping VS Build Tools install.")
            return True
        licence = self._licence_of(winget, _VS_BUILD_TOOLS_ID)
        if licence is None or not is_accepted(ctx.consent, licence):
            self._console.error("Visual Studio Build Tools need consent to their licence"
                                + (f": {licence.link}" if licence else "."))
            return False

        vs_cmd = [
            "winget", "install",
            "--id", _VS_BUILD_TOOLS_ID, "-e",
            "--accept-package-agreements", "--accept-source-agreements",
            "--override",
            "--add Microsoft.VisualStudio.Workload.VCTools "
            "--includeRecommended --quiet --wait --norestart",
        ]
        with self._console.console.status(
            "[header]Installing Visual Studio Build Tools "
            "(C++ workloads) — this may take 10–20 minutes.",
            spinner="bouncingBar",
        ):
            rc = self._actions.run_command(vs_cmd)
        if rc != 0:
            self._console.warn("Visual Studio Build Tools install failed or was cancelled.")
            return False
        self._console.success("Visual Studio Build Tools installed.")
        return True

    @staticmethod
    def _licence_of(winget: IPackageManager, pkg: str) -> Licence | None:
        """Returns the licence *winget* names for *pkg*; None when it names none."""
        return winget.licence_of(pkg) if isinstance(winget, IWingetLicences) else None

    def _vs_build_tools_missing(self, winget: IPackageManager) -> bool:
        """Report whether no Visual Studio C++ toolset is found and winget lists no Build Tools."""
        if self._actions.find_vcvars() is not None:
            return False
        return not winget.is_installed(_VS_BUILD_TOOLS_ID)
