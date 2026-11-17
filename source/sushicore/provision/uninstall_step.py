# uninstall_step.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Removes the packages and files an install run placed on this system."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any, Callable

from . import home
from ._output import console
from .dependency_presence import available_linux_manager, named_manager
from .fragments import IDependencySource
from .package_lists import dedup
from .packages import IPackageManager, tools_dir
from .pipeline import InstallContext, Step, StepResult
from .sinks import ConfigSink


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

    def run(self, ctx: InstallContext) -> StepResult:
        """Dispatch to the Linux or Windows uninstall routine for this platform."""
        if ctx.cfg.platform == "windows":
            return self._run_windows(ctx)
        return self._run_linux(ctx)

    def _run_linux(self, ctx: InstallContext) -> StepResult:
        """Remove Linux packages and vcpkg ports, and toolchains too with ``ctx.everything``."""
        if not _root_is_safe(self._console, self._root):
            return StepResult.FAILED
        mgr = available_linux_manager(self._managers)
        vcpkg = named_manager(self._managers, "vcpkg")
        pkgs: list[str] = []
        vcpkg_ports: list[str] = []
        for dep in self._source.selected("linux", ctx.gpu):
            pkgs.extend(mgr.translate_apt(dep.linux_apt) if mgr else dep.linux_apt)
            vcpkg_ports.extend(dep.vcpkg_fallback_ports("linux"))
        pkgs = dedup(pkgs)
        vcpkg_ports = dedup(vcpkg_ports)

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
        vcpkg = named_manager(self._managers, "vcpkg")

        ports: list[str] = []
        for dep in self._source.selected("windows", ctx.gpu):
            ports.extend(dep.windows_vcpkg)
        ports = dedup(ports)

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
