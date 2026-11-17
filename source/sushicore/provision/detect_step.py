# detect_step.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Inventories the tools and dependencies of a machine for an install run."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Callable

from rich.markup import escape

from .default_console import console_or_default
from . import home, probe, selection
from ..proc import CommandRunner
from ..quiet_runner import quiet_runner
from .config import ProvisionConfig
from .dependency_presence import check_cmd_ok, dep_installed, dep_manager, vcpkg_manager
from .fragments import SHARED_OWNER, Dependency, IDependencySource, owner_order
from .gpu_vendor import detect_gpu_vendor
from .packages import IPackageManager, refresh_windows_path
from .install_context import InstallContext
from .provision_console import ProvisionConsole
from .step import Step
from .step_result import StepResult
from .target import target_of


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


def _literal(text: str, out: ProvisionConsole) -> str:
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
                 *, toolchain_status: Callable[[ProvisionConfig, bool], list[tuple[str, bool, str]]] = probe.toolchain_status,
                 gpu_vendor: Callable[[], str] = detect_gpu_vendor, console: ProvisionConsole | None = None,
                 runner: CommandRunner | None = None) -> None:
        """Wire the dependency source, the package managers and the machine probes.

        Args:
            after_inventory: Called with the context and the full dependency
                list once the inventory table has been printed.
            toolchain_status: Reads the SYCL toolchains off the machine.
            gpu_vendor: Reads the discrete-GPU vendor off the machine.
            console: The console the step prints through.
            runner: Runs each dependency's check command; the quiet runner when ``None``.
        """
        console = console_or_default(console, "DetectStep")
        self._source = source
        self._managers = managers or []
        self._after_inventory = after_inventory
        self._toolchain_status = toolchain_status
        self._gpu_vendor = gpu_vendor
        self._console = console
        self._runner = runner if runner is not None else quiet_runner()

    def _dep_manager(self, plat: str) -> IPackageManager | None:
        """Return the manager that knows whether a manifest dep is installed."""
        return dep_manager(self._managers, plat)

    def _vcpkg_manager(self) -> IPackageManager | None:
        """Return the vcpkg manager, if wired in."""
        return vcpkg_manager(self._managers)

    def _base_tool_rows(self, ctx: InstallContext,
                        owner_of: Callable[[str], str]) -> list[tuple[str, str, str, str]]:
        """Probe the tools a build invokes directly and return their rows."""
        cfg = ctx.cfg
        configured = {
            "cmake":     cfg.expand(cfg.cmake_exe)    if cfg.cmake_exe    else "",
            "ninja":     cfg.expand(cfg.ninja_exe)    if cfg.ninja_exe    else "",
            "pkg-config": cfg.expand(cfg.pkgconf_exe) if cfg.pkgconf_exe  else "",
            "doxygen":   cfg.expand(cfg.doxygen_exe)  if cfg.doxygen_exe  else "",
        }
        rows: list[tuple[str, str, str, str]] = []
        for tool in (target_of(cfg).python_executable,
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
                        owner_of: Callable[[str], str]) -> list[tuple[str, str, str, str]]:
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
                present = dep_installed(dep, dep_mgr, plat, vcpkg_mgr)
            else:
                present = bool(dep.check_cmd) and check_cmd_ok(dep.check_cmd, self._runner)
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
        self._console.info(target_of(ctx.cfg).system_prerequisites_note)

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
