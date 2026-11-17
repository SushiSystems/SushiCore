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
from .fragments import IDependencySource
from .packages import IPackageManager
from .pipeline import InstallContext, Step, StepResult
from .sinks import ConfigSink
from .target import target_of
from .uninstall_plan import UNINSTALL_PLANS, UninstallServices


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
        self._services = UninstallServices(source=source, managers=managers, console=console)
        self._sink = sink
        self._console = console
        self._root = root or (lambda: home.root())

    def run(self, ctx: InstallContext) -> StepResult:
        """Remove the target's packages, then the toolchains with ``ctx.everything``, then the config."""
        if not _root_is_safe(self._console, self._root):
            return StepResult.FAILED
        UNINSTALL_PLANS.plan_for(target_of(ctx.cfg)).remove_packages(ctx, self._services)
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
