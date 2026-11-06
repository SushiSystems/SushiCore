# steps.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Shared install steps: detect, install-deps, configure, uninstall."""

from __future__ import annotations

import dataclasses
import shutil
import subprocess
from pathlib import Path
from typing import Any, Callable

from rich.markup import escape

from . import home, probe
from ._output import console
from .download_verifier import DownloadVerifier, bind_verifier
from .fragments import SHARED_OWNER, Dependency, IDependencySource, owner_order
from .gpu.adapter_builder import AdapterBuilder, SubprocessCommandRunner
from .gpu.provisioning import provision_gpu_adapters
from .gpu.registry import DEFAULT_REGISTRY
from .packages import (
    IPackageManager,
    LinuxPackageManager,
    WINGET_ID_TO_CMD,
    tools_dir,
    ensure_intel_oneapi_repo,
    install_gpu_stack,
    refresh_windows_path,
)
from . import selection
from .pipeline import InstallContext, Step, StepResult
from .sinks import ConfigSink, render_local_config
from .toolchains import adaptivecpp, intel_llvm, oneapi

#: System toolchain installed through the toolchain manager, not the manifest.
_LINUX_TOOLCHAIN_APT = ["build-essential", "cmake", "ninja-build", "git"]


@dataclasses.dataclass(frozen=True)
class MachineActions:
    """The calls the steps make that reach the machine, each replaceable by a test.

    Every default looks its function up when called, so a replacement made on the
    module that owns the function still takes effect.

    Attributes:
        refresh_path: Reloads ``PATH`` from the registry (Windows only).
        which: Finds an executable on ``PATH``; ``None`` when absent.
        find_vcvars: Finds the Visual Studio C++ tools script; ``None`` when absent.
        run_command: Runs a command line and returns an object with ``returncode``.
        resolve_config: Probes the machine-specific tool paths of a configuration.
        install_oneapi: Installs Intel oneAPI for a run; returns whether it succeeded.
        detect_vendor: Reads the discrete-GPU vendor off the machine.
    """

    refresh_path: Callable[[], None] = lambda: refresh_windows_path()
    which: Callable[[str], str | None] = lambda name: shutil.which(name)
    find_vcvars: Callable[[], Path | None] = lambda: probe.find_vcvars()
    run_command: Callable[..., Any] = lambda cmd: subprocess.run(cmd)
    resolve_config: Callable[..., dict[str, str]] = (
        lambda cfg, gpu=False: probe.resolve_local_config(cfg, gpu=gpu))
    install_oneapi: Callable[[InstallContext], bool] = lambda ctx: oneapi.install_oneapi(ctx)
    detect_vendor: Callable[[], str] = lambda: probe.detect_gpu_vendor()


def _subprocess_builder(cfg: Any) -> AdapterBuilder:
    """Return the adapter builder that runs its commands as processes."""
    return AdapterBuilder(cfg=cfg, runner=SubprocessCommandRunner())


def provision_adapters_for_run(
        ctx: InstallContext, *, console: Any = console,
        actions: MachineActions | None = None,
        make_builder: Callable[[Any], Any] = _subprocess_builder,
        build_adapters: Callable[..., None] | None = None) -> None:
    """Build every located GPU backend's Unified Runtime adapter for this run.

    Args:
        console: The console the skip message is printed through.
        actions: The machine calls; the real ones when omitted.
        make_builder: Builds the adapter builder from the probed configuration.
        build_adapters: Builds the adapters of one toolchain; defaults to
            :func:`sushicore.provision.gpu.provisioning.provision_gpu_adapters`.
    """
    actions = actions or MachineActions()
    build_adapters = build_adapters or provision_gpu_adapters
    actions.refresh_path()
    probed = actions.resolve_config(ctx.cfg, gpu=ctx.gpu)
    llvm_root = ctx.resolved_paths.get("llvm_root") or probed.get("llvm_root")
    if not llvm_root:
        console.info("No intel/llvm toolchain installed; GPU adapter build skipped.")
        return
    held = {field.name for field in dataclasses.fields(ctx.cfg)}
    cfg = dataclasses.replace(ctx.cfg, **{key: value for key, value in probed.items() if key in held})
    build_adapters(cfg, DEFAULT_REGISTRY, Path(llvm_root), make_builder(cfg), ctx.dry_run)


def _resolve_gpu_vendor(ctx: InstallContext, detect: Callable[[], str]) -> str:
    """Return the GPU vendor the detect step recorded, probing the machine when it did not."""
    ctx.gpu_vendor = ctx.gpu_vendor or detect() or "none"
    return ctx.gpu_vendor


class GpuStage:
    """The GPU part of an install run: the compute SDK, then the adapter builds.

    Args:
        console: The console the warnings are printed through.
        actions: The machine calls; the real ones when omitted.
        install_stack: Installs the compute SDK of a vendor; defaults to
            :func:`sushicore.provision.packages.install_gpu_stack`.
        provision_adapters: Builds the adapters for a run; defaults to
            :func:`provision_adapters_for_run`.
    """

    def __init__(self, *, console: Any = console, actions: MachineActions | None = None,
                 install_stack: Callable[..., bool] | None = None,
                 provision_adapters: Callable[[InstallContext], None] | None = None) -> None:
        """Wire the console, the machine calls and the two GPU actions."""
        self._console = console
        self._actions = actions or MachineActions()
        self._install_stack = install_stack or (
            lambda cfg, vendor, dry_run: install_gpu_stack(cfg, vendor, dry_run))
        self._provision_adapters = provision_adapters or (
            lambda ctx: provision_adapters_for_run(
                ctx, console=self._console, actions=self._actions))

    def provision_linux(self, ctx: InstallContext, manager_name: str) -> None:
        """Install the GPU SDK through the manager named *manager_name*, then build the adapters.

        Nothing is installed when the run did not select the GPU; the SDK is automated
        on ``apt`` only.
        """
        vendor = _resolve_gpu_vendor(ctx, self._actions.detect_vendor) if ctx.gpu else "none"
        if ctx.gpu and manager_name == "apt":
            if not self._install_stack(ctx.cfg, vendor, ctx.dry_run) and vendor != "none":
                message = (f"GPU compute SDK for '{vendor}' was not installed — "
                           f"the build will fall back to the CPU (SPIR/OpenCL) path. "
                           f"See the log above for the failing command.")
                self._console.error(message)
                ctx.warnings.append(message)
        elif ctx.gpu and vendor == "none":
            self._install_stack(ctx.cfg, vendor, ctx.dry_run)
        elif ctx.gpu:
            self._console.warn(f"GPU SDK auto-install for '{vendor}' is only "
                               f"automated on apt; install it manually on {manager_name}.")
        if vendor != "none":
            self._provision_adapters(ctx)

    def provision_windows(self, ctx: InstallContext) -> None:
        """Install the GPU SDK, then build the adapters, when the run selected the GPU."""
        if not ctx.gpu:
            return
        vendor = _resolve_gpu_vendor(ctx, self._actions.detect_vendor)
        self._install_stack(ctx.cfg, vendor, ctx.dry_run)
        if vendor != "none":
            self._provision_adapters(ctx)


def _check_cmd_ok(cmd: list[str]) -> bool:
    """Return True if *cmd* runs and exits 0."""
    try:
        return subprocess.run(cmd, capture_output=True).returncode == 0
    except (OSError, FileNotFoundError):
        return False


def _dep_installed(dep: Dependency, mgr: IPackageManager | None, platform: str,
                   vcpkg: IPackageManager | None = None) -> bool:
    """Return whether *dep* is already installed on this platform."""
    if dep.check_cmd and _check_cmd_ok(dep.check_cmd):
        return True
    return _manager_holds(dep, mgr, platform, vcpkg)


def _manager_holds(dep: Dependency, mgr: IPackageManager | None, platform: str,
                   vcpkg: IPackageManager | None = None) -> bool:
    """Return whether a package manager reports every package of *dep* installed."""
    pkgs = dep.packages_for(platform)
    if pkgs:
        return mgr is not None and all(mgr.is_installed(p) for p in pkgs)
    fallback = dep.vcpkg_fallback_ports(platform)
    if fallback:
        return vcpkg is not None and all(vcpkg.is_installed(p) for p in fallback)
    return False


#: The Linux managers that can answer whether a manifest package is installed.
_LINUX_MANAGERS = ("apt", "dnf", "yum", "pacman", "zypper")


def _vcpkg_manager(managers: list[IPackageManager]) -> IPackageManager | None:
    """Return the vcpkg manager among *managers*, if wired in."""
    return next((m for m in managers if m.name == "vcpkg"), None)


def _dep_manager(managers: list[IPackageManager], platform: str) -> IPackageManager | None:
    """Return the manager that knows whether a manifest dependency is installed."""
    if platform == "windows":
        return _vcpkg_manager(managers)
    return next((m for m in managers if m.name in _LINUX_MANAGERS and m.available()), None)


def held_by_managers(managers: list[IPackageManager],
                     platform: str) -> Callable[[Dependency], bool]:
    """Return the predicate telling whether *managers* report a dependency installed."""
    mgr = _dep_manager(managers, platform)
    vcpkg = _vcpkg_manager(managers)
    return lambda dep: _manager_holds(dep, mgr, platform, vcpkg)


#: The three statuses an inventory row can carry.
_OK = "OK"
_MISSING = "MISSING"
_NOT_NEEDED = "NOT NEEDED"

#: How the summary line names a status; a status not listed is named by its own text.
_SUMMARY_LABELS = {_MISSING: "missing", _NOT_NEEDED: "not needed"}

#: One inventory row: component, status, owner, detail.
_Row = tuple[str, str, str, str]

#: What each discrete-GPU vendor implies for the compute SDK that gets installed.
_VENDOR_SDK = {
    "amd":  "AMD — installs ROCm (HIP)",
    "intel": "Intel — installs Level Zero + Intel OpenCL",
    "none": "no discrete GPU — CPU (SPIR/OpenCL) path",
}

#: NVIDIA's row names how each platform installs the toolkit.
_VENDOR_SDK_NVIDIA = {
    "windows": "NVIDIA — installs CUDA toolkit (NVIDIA installer, one UAC prompt)",
    "linux":   "NVIDIA — installs CUDA toolkit (NVIDIA apt repo)",
}


def _status(present: bool) -> str:
    """Return the status a probed component reports."""
    return _OK if present else _MISSING


def _literal(text: str, out: Any) -> str:
    """Return *text* ready for ``out.info``: escaped on a terminal, untouched in JSON events."""
    return text if out.is_machine() else escape(text)


def _rerun_command(ctx: InstallContext) -> str:
    """Return the command that re-runs provisioning: the one *ctx* names, else the program's ``setup``."""
    return ctx.rerun_command or f"{ctx.program} setup".strip()


def removal_note(ctx: InstallContext) -> str:
    """Return the note on removing the whole install, with the consumer's own hint after it."""
    return f"Remove the whole install by deleting that folder. {ctx.removal_hint}".strip()


class DetectStep(Step):
    """Inventory tools and dependencies; fill ``ctx.detected``."""

    name = "detect"

    def __init__(self, source: IDependencySource,
                 managers: list[IPackageManager] | None = None,
                 after_inventory: Callable[[InstallContext, list[Dependency]], None] | None = None,
                 *, toolchain_status=probe.toolchain_status,
                 gpu_vendor=probe.detect_gpu_vendor, console: Any = console) -> None:
        """Wire the dependency source, the package managers and the machine probes.

        Args:
            after_inventory: Called with the context and the full dependency
                list once the inventory table has been printed.
            toolchain_status: Reads the SYCL toolchains off the machine.
            gpu_vendor: Reads the discrete-GPU vendor off the machine.
            console: The console the step prints through.
        """
        self._source = source
        self._managers = managers or []
        self._after_inventory = after_inventory
        self._toolchain_status = toolchain_status
        self._gpu_vendor = gpu_vendor
        self._console = console

    def _dep_manager(self, plat: str) -> IPackageManager | None:
        """Return the manager that knows whether a manifest dep is installed."""
        return _dep_manager(self._managers, plat)

    def _vcpkg_manager(self) -> IPackageManager | None:
        """Return the vcpkg manager, if wired in."""
        return _vcpkg_manager(self._managers)

    def _base_tool_rows(self, ctx: InstallContext,
                        owner_of) -> list[tuple[str, str, str, str]]:
        """Probe the tools a build invokes directly and return their rows."""
        cfg = ctx.cfg
        configured = {
            "cmake":     cfg.expand(cfg.cmake_exe)    if cfg.cmake_exe    else "",
            "ninja":     cfg.expand(cfg.ninja_exe)    if cfg.ninja_exe    else "",
            "pkg-config": cfg.expand(cfg.pkgconf_exe) if cfg.pkgconf_exe  else "",
            "doxygen":   cfg.expand(cfg.doxygen_exe)  if cfg.doxygen_exe  else "",
        }
        rows: list[tuple[str, str, str, str]] = []
        for tool in ("python3" if cfg.platform != "windows" else "python",
                     "git", "cmake", "ninja", "pkg-config", "doxygen"):
            path = shutil.which(tool) or ""
            if not path and configured.get(tool) and Path(configured[tool]).is_file():
                path = configured[tool]
            ctx.detected[tool] = bool(path)
            rows.append((tool, _status(bool(path)), owner_of(tool), path))
        return rows

    def _sycl_compiler_row(self, ctx: InstallContext) -> tuple[str, str, str, str]:
        """Probe the SYCL compiler a build would use and return its row."""
        compiler, where = probe.find_sycl_compiler(ctx.cfg)
        if compiler is None:
            compiler, where = probe.find_configured_toolchain(ctx.cfg)
        ctx.detected["sycl_compiler"] = compiler is not None
        return ("SYCL compiler (active)", _status(compiler is not None), "sushiruntime",
                f"{compiler or '-'} {where or ''}".strip())

    def _toolchain_rows(self, ctx: InstallContext, declared: set[str],
                        owner_of) -> list[tuple[str, str, str, str]]:
        """Return a row per SYCL toolchain (and CUDA), recording what is present.

        A declared toolchain that is absent while another member of its
        capability is present is not needed, and its row says what provides it.
        """
        status = list(self._toolchain_status(ctx.cfg, ctx.gpu))
        present = {name for name, found, _detail in status if found}
        provided_by = {
            member: (capability, next(m for m in members if m in present))
            for capability, members in selection.groups(self._source).items()
            if present.intersection(members)
            for member in members if member not in present
        }
        rows: list[tuple[str, str, str, str]] = []
        for name, found, detail in status:
            ctx.detected[name] = found
            if name not in declared:
                rows.append((name, _NOT_NEEDED, owner_of(name),
                             detail or "no present module declares it"))
            elif name in provided_by:
                capability, provider = provided_by[name]
                rows.append((name, _NOT_NEEDED, owner_of(name),
                             f"{detail} ({provider} provides {capability})"))
            else:
                rows.append((name, _status(found), owner_of(name), detail))
        return rows

    def _dependency_rows(self, ctx: InstallContext,
                         all_deps: list[Dependency]) -> list[tuple[str, str, str, str]]:
        """Return a row per declared dependency, recording the installable ones."""
        plat = ctx.cfg.platform
        dep_mgr = self._dep_manager(plat)
        vcpkg_mgr = self._vcpkg_manager()
        installable = {d.name for d in self._source.selected(plat, ctx.gpu)}

        rows: list[tuple[str, str, str, str]] = []
        for dep in all_deps:
            if dep.name not in installable:
                rows.append((dep.name, _NOT_NEEDED, dep.owner,
                             f"{dep.description} (nothing to install on {plat})"))
                continue
            if dep_mgr is not None or vcpkg_mgr is not None:
                present = _dep_installed(dep, dep_mgr, plat, vcpkg_mgr)
            else:
                present = bool(dep.check_cmd) and _check_cmd_ok(dep.check_cmd)
            ctx.detected[dep.name] = present
            pkgs = ", ".join(dep.packages_for(plat) or dep.vcpkg_fallback_ports(plat))
            rows.append((dep.name, _status(present), dep.owner,
                         f"{dep.description} ({pkgs})"))
        return rows

    def _gpu_vendor_row(self, ctx: InstallContext) -> tuple[str, str, str, str]:
        """Probe the discrete-GPU vendor and return its row."""
        vendor = self._gpu_vendor()
        ctx.gpu_vendor = vendor
        ctx.detected["nvidia_gpu"] = vendor == "nvidia"
        if vendor == "nvidia":
            detail = _VENDOR_SDK_NVIDIA.get(ctx.cfg.platform, _VENDOR_SDK_NVIDIA["linux"])
        else:
            detail = _VENDOR_SDK.get(vendor, vendor)
        return ("GPU vendor", _status(vendor != "none"), SHARED_OWNER, detail)

    def inventory_rows(self, ctx: InstallContext,
                       all_deps: list[Dependency]) -> list[tuple[str, str, str, str]]:
        """Probe the machine and return ``(component, status, owner, detail)`` rows."""
        owner_by_name = {dep.name: dep.owner for dep in all_deps}
        declared = {dep.name for dep in all_deps if dep.owner != SHARED_OWNER}

        def owner_of(name: str) -> str:
            return owner_by_name.get(name, SHARED_OWNER)

        collected = list(self._base_tool_rows(ctx, owner_of))
        if "sushiruntime" in {dep.owner for dep in all_deps}:
            collected.append(self._sycl_compiler_row(ctx))
        collected.extend(self._toolchain_rows(ctx, declared, owner_of))
        collected.extend(self._dependency_rows(ctx, all_deps))
        collected.append(self._gpu_vendor_row(ctx))

        unique: dict[str, tuple[str, str, str, str]] = {}
        for row in collected:
            unique.setdefault(row[0], row)

        by_owner: dict[str, list[tuple[str, str, str, str]]] = {}
        for row in unique.values():
            by_owner.setdefault(row[2], []).append(row)
        return [row for owner in owner_order(self._source, by_owner)
                for row in by_owner[owner]]

    @staticmethod
    def summarize_inventory(rows: list[_Row]) -> tuple[dict[str, int], list[_Row]]:
        """Count the inventory rows by status text and pick out the missing ones.

        Args:
            rows: The rows the inventory table shows, as ``inventory_rows`` returned them.

        Returns:
            The count per status, ordered OK, MISSING, NOT NEEDED and then any other
            status by first appearance, with no zero counts; and the MISSING rows in
            table order.
        """
        seen: dict[str, int] = {}
        for _component, status, _owner, _detail in rows:
            seen[status] = seen.get(status, 0) + 1
        known = (_OK, _MISSING, _NOT_NEEDED)
        ordered = [status for status in known if status in seen]
        ordered += [status for status in seen if status not in known]
        return ({status: seen[status] for status in ordered},
                [row for row in rows if row[1] == _MISSING])

    def run(self, ctx: InstallContext) -> StepResult:
        """Probe the machine, print the inventory table, and report it upward."""
        refresh_windows_path()
        all_deps = self._source.all()

        rows = self.inventory_rows(ctx, all_deps)
        self._console.table(
            ["Component", "Status", "Owner", "Detail"],
            [list(row) for row in rows],
            title="Environment inventory",
            group_by="Owner",
        )

        self._console.info(f"Vendored dependencies go in one folder: {home.root()}")
        self._console.info(removal_note(ctx))
        if ctx.cfg.platform == "windows":
            self._console.info("System prerequisites kept outside that folder: the C++ "
                         "host compiler (Visual Studio Build Tools + Windows SDK), "
                         "git, and the toolkit for the detected GPU.")
        else:
            self._console.info("System prerequisites kept outside that folder: the host "
                         "compiler (gcc) plus the -dev packages (hwloc, gtest, "
                         "opencl), git, and the toolkit for the detected GPU.")

        self.report_inventory(ctx, rows)
        if self._after_inventory is not None:
            self._after_inventory(ctx, all_deps)
        return StepResult.OK

    def report_inventory(self, ctx: InstallContext, rows: list[_Row]) -> None:
        """Print the one-line summary of *rows* and, when any is missing, what to do about it."""
        counts, missing = self.summarize_inventory(rows)
        self._console.info(" | ".join(f"{count} {_SUMMARY_LABELS.get(status, status)}"
                               for status, count in counts.items()))
        if not missing:
            return
        self._console.warn("Needs attention")
        for component, _status_text, _owner, detail in missing:
            self._console.info(_literal(f"{component}  {detail}".rstrip(), self._console))
        self._console.info(f"Run `{_rerun_command(ctx)}` to provision what is missing.")


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

    def _manager(self, name: str) -> IPackageManager | None:
        """Return the wired manager named *name*, or None."""
        for m in self._managers:
            if m.name == name:
                return m
        return None

    def run(self, ctx: InstallContext) -> StepResult:
        """Run the install routine of this platform with the fragments' digests bound.

        Raises:
            DigestMismatchError: A download's SHA-256 is not the one its entry pins.
        """
        bind_verifier(DownloadVerifier(self._source.digests(ctx.cfg.platform)))
        try:
            if ctx.cfg.platform == "windows":
                return self._run_windows(ctx)
            return self._run_linux(ctx)
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
                assume_yes=ctx.assume_acpp_llvm)
            if acpp:
                ctx.resolved_paths["acpp_exe"] = acpp
            elif not ctx.selection.install_intel_llvm:
                message = ("AdaptiveCpp is the only toolchain selected but it did "
                           "not install; the project will not build.")
                self._console.warn(f"{message} {ctx.fallback_hint}".strip())

    def _run_linux(self, ctx: InstallContext) -> StepResult:
        """Install dependencies, the toolchains and the GPU stack on Linux."""
        linux_managers = ["apt", "dnf", "yum", "pacman", "zypper"]
        mgr = next(
            (self._manager(n) for n in linux_managers
             if self._manager(n) and self._manager(n).available()),  # type: ignore[union-attr]
            None,
        )
        if mgr is None:
            msg = ("No supported package manager found (apt, dnf, yum, pacman, zypper). "
                   "Install python3, pip, git, cmake, and ninja manually, then re-run.")
            if ctx.dry_run:
                self._console.warn(f"(dry-run) {msg}")
                return StepResult.SKIPPED
            self._console.error(msg)
            return StepResult.FAILED
        assert isinstance(mgr, LinuxPackageManager)  # linux_managers only holds these

        self._console.info(f"Using package manager: {mgr.name}")
        vcpkg = self._manager("vcpkg")

        # Translate the generic apt toolchain list to native package names.
        pkgs: list[str] = list(mgr.translate_apt(_LINUX_TOOLCHAIN_APT))
        vcpkg_ports: list[str] = []
        for dep in self._source.selected("linux", ctx.gpu):
            if _dep_installed(dep, mgr, "linux", vcpkg):
                self._console.info(f"{dep.name}: already installed, skipping.")
                continue
            if dep.linux_apt:
                pkgs.extend(mgr.translate_apt(dep.linux_apt))
            else:
                vcpkg_ports.extend(dep.vcpkg_fallback_ports("linux"))

        pkgs = _dedup(pkgs)
        vcpkg_ports = _dedup(vcpkg_ports)

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

        if ctx.selection.oneapi and mgr.name == "apt":
            self._console.info("oneAPI: configuring the Intel apt repository and installing "
                         "intel-oneapi-compiler-dpcpp-cpp.")
            if ensure_intel_oneapi_repo(ctx.dry_run):
                if not mgr.install(["intel-oneapi-compiler-dpcpp-cpp"], ctx.dry_run):
                    self._console.warn("oneAPI compiler install failed; continuing "
                                 "(intel-llvm/AdaptiveCpp remain available).")
        elif ctx.selection.oneapi:
            self._console.warn(f"oneAPI on {mgr.name} is not automated; install the "
                         "Intel oneAPI DPC++ compiler manually.")

        self._gpu.provision_linux(ctx, mgr.name)
        return StepResult.OK if ok else StepResult.FAILED

    def _run_windows(self, ctx: InstallContext) -> StepResult:
        """Install dependencies, the toolchains and the GPU stack on Windows."""
        self._actions.refresh_path()
        winget = self._manager("winget")
        direct = self._manager("direct-download")
        vcpkg  = self._manager("vcpkg")

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
            if vcpkg and _dep_installed(dep, vcpkg, "windows"):
                self._console.info(f"{dep.name}: already installed, skipping.")
                continue
            ports.extend(dep.windows_vcpkg)
        ports = _dedup(ports)

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
        if self._actions.find_vcvars() is not None:
            return True
        if not (winget and winget.available()):
            return True
        if winget.is_installed("Microsoft.VisualStudio.2022.BuildTools"):
            return True
        if ctx.dry_run:
            self._console.info("(dry-run) skipping VS Build Tools install.")
            return True

        vs_cmd = [
            "winget", "install",
            "--id", "Microsoft.VisualStudio.2022.BuildTools", "-e",
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
            rc = self._actions.run_command(vs_cmd).returncode
        if rc != 0:
            self._console.warn("Visual Studio Build Tools install failed or was cancelled.")
            return False
        self._console.success("Visual Studio Build Tools installed.")
        return True


class ConfigureStep(Step):
    """Probe installed tools and write them through a :class:`ConfigSink`."""

    name = "configure"

    def __init__(self, sink: ConfigSink, *, console: Any = console,
                 actions: MachineActions | None = None) -> None:
        """Bind this step to the sink its probed values and active toolchain are written to.

        Args:
            console: The console the step prints through.
            actions: The machine calls; the real ones when omitted.
        """
        self._sink = sink
        self._console = console
        self._actions = actions or MachineActions()

    def run(self, ctx: InstallContext) -> StepResult:
        """Probe machine-specific tool paths and write them and the active toolchain to the sink."""
        self._actions.refresh_path()
        values = self._actions.resolve_config(ctx.cfg, gpu=ctx.gpu)
        ctx.resolved_paths = values

        if ctx.dry_run:
            if ctx.active_toolchain:
                self._console.info(f"(dry-run) would set active toolchain to "
                             f"'{ctx.active_toolchain}'.")
            if values:
                self._console.info(f"(dry-run) would write {self._sink.target}:")
                self._console.console.print(
                    render_local_config(ctx.cfg.platform, values), markup=False)
            return StepResult.OK

        if not values and not ctx.active_toolchain:
            self._console.info("No machine-specific paths to write; defaults suffice.")
            return StepResult.SKIPPED

        if values:
            backup = self._sink.backup()
            if backup is not None:
                self._console.info(f"Backed up existing config to {backup.name}")
            written = self._sink.write_paths(ctx.cfg.platform, values)
            self._console.success(f"Wrote {written}")

        if ctx.active_toolchain:
            self._sink.write_tool({"toolchain": ctx.active_toolchain})
            self._console.success(f"Active SYCL toolchain set to '{ctx.active_toolchain}'.")
        return StepResult.OK


class UninstallStep(Step):
    """Remove packages and files that the installer placed on this system."""

    name = "uninstall"

    def __init__(self, source: IDependencySource,
                 managers: list[IPackageManager], sink: ConfigSink,
                 *, console: Any = console,
                 root: Callable[[], Path] | None = None) -> None:
        """Wire the dependency source, the package managers and the sink this step clears.

        Args:
            console: The console the step prints through.
            root: Returns the dependency root this step may remove; the bound root when omitted.
        """
        self._source = source
        self._managers = managers
        self._sink = sink
        self._console = console
        self._root = root or (lambda: home.root())

    def _manager(self, name: str) -> IPackageManager | None:
        """Return the wired manager named *name*, or None."""
        for m in self._managers:
            if m.name == name:
                return m
        return None

    def run(self, ctx: InstallContext) -> StepResult:
        """Dispatch to the Linux or Windows uninstall routine for this platform."""
        if ctx.cfg.platform == "windows":
            return self._run_windows(ctx)
        return self._run_linux(ctx)

    def _run_linux(self, ctx: InstallContext) -> StepResult:
        """Remove Linux packages and vcpkg ports, and toolchains too with ``ctx.everything``."""
        if not _root_is_safe(self._console, self._root):
            return StepResult.FAILED
        linux_names = ["apt", "dnf", "yum", "pacman", "zypper"]
        mgr = next(
            (self._manager(n) for n in linux_names
             if self._manager(n) and self._manager(n).available()),  # type: ignore[union-attr]
            None,
        )
        assert mgr is None or isinstance(mgr, LinuxPackageManager)  # linux_names only holds these
        vcpkg = self._manager("vcpkg")
        pkgs: list[str] = []
        vcpkg_ports: list[str] = []
        for dep in self._source.selected("linux", ctx.gpu):
            pkgs.extend(mgr.translate_apt(dep.linux_apt) if mgr else dep.linux_apt)
            vcpkg_ports.extend(dep.vcpkg_fallback_ports("linux"))
        pkgs = _dedup(pkgs)
        vcpkg_ports = _dedup(vcpkg_ports)

        if mgr and pkgs:
            self._console.info(f"Removing via {mgr.name}: {', '.join(pkgs)}")
            mgr.remove(pkgs, ctx.dry_run)

        if vcpkg and vcpkg_ports:
            self._console.info(f"Removing vcpkg ports: {', '.join(vcpkg_ports)}")
            vcpkg.remove(vcpkg_ports, ctx.dry_run)

        if ctx.everything:
            if not self._remove_installed_toolchains(ctx):
                return StepResult.FAILED
        self._remove_config(ctx)
        return StepResult.OK

    def _run_windows(self, ctx: InstallContext) -> StepResult:
        """Remove Windows vcpkg ports, portable tools, and toolchains with ``ctx.everything``."""
        if not _root_is_safe(self._console, self._root):
            return StepResult.FAILED
        vcpkg = self._manager("vcpkg")

        ports: list[str] = []
        for dep in self._source.selected("windows", ctx.gpu):
            ports.extend(dep.windows_vcpkg)
        ports = _dedup(ports)

        if vcpkg and ports:
            self._console.info(f"Removing vcpkg ports: {', '.join(ports)}")
            vcpkg.remove(ports, ctx.dry_run)

        tools = tools_dir()
        ninja_exe = tools / "ninja.exe"
        if ninja_exe.is_file():
            if ctx.dry_run:
                self._console.info(f"(dry-run) would remove {ninja_exe}")
            else:
                ninja_exe.unlink()
                self._console.info(f"Removed {ninja_exe}")
        cmake_dir = tools / "cmake"
        if cmake_dir.is_dir():
            if ctx.dry_run:
                self._console.info(f"(dry-run) would remove {cmake_dir}")
            else:
                shutil.rmtree(cmake_dir, ignore_errors=True)
                self._console.info(f"Removed {cmake_dir}")
        doxygen_dir = tools / "doxygen"
        if doxygen_dir.is_dir():
            if ctx.dry_run:
                self._console.info(f"(dry-run) would remove {doxygen_dir}")
            else:
                shutil.rmtree(doxygen_dir, ignore_errors=True)
                self._console.info(f"Removed {doxygen_dir}")
        if tools.is_dir() and not any(tools.iterdir()) and not ctx.dry_run:
            tools.rmdir()

        if ctx.everything:
            if not self._remove_installed_toolchains(ctx):
                return StepResult.FAILED

        self._remove_config(ctx)
        return StepResult.OK

    def _remove_installed_toolchains(self, ctx: InstallContext) -> bool:
        """Delete the whole vendored dependency tree, refusing an unsafe root.

        Returns:
            False when *ctx*'s dependency root fails the removability guard;
            True otherwise, whether or not anything was actually removed.
        """
        dep_dir = self._root()
        if not dep_dir.is_dir():
            return True
        if not _root_is_safe(self._console, self._root):
            return False
        if ctx.dry_run:
            self._console.info(f"(dry-run) would remove the whole deps folder at {dep_dir}")
            return True
        shutil.rmtree(dep_dir, ignore_errors=True)
        self._console.success(f"Removed the vendored deps folder at {dep_dir}")
        return True

    def _remove_config(self, ctx: InstallContext) -> None:
        """Clear the sink's ``[tool]`` table, leaving the rest of its file intact."""
        if ctx.dry_run:
            self._console.info(f"(dry-run) would clear the `tool` section of {self._sink.target}")
            return
        self._sink.clear()
        self._console.success(f"Cleared the `tool` section of {self._sink.target}")


def _root_is_safe(out: Any, root: Callable[[], Path]) -> bool:
    """Return whether the dependency root is absent or passes the removability guard."""
    dep_dir = root()
    if not dep_dir.is_dir() or home.is_removable_root(dep_dir):
        return True
    out.error(f"Refusing to remove {dep_dir}: not a safe dependency root.")
    return False


def _dedup(items: list[str]) -> list[str]:
    """Return *items* with duplicates removed, keeping first-seen order."""
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out
