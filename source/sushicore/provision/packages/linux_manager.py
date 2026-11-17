# linux_manager.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The contract a Linux package manager implements on top of the package-manager one."""

from __future__ import annotations

from typing import Any

from sushicore.proc import CommandRunner

from ..default_console import console_or_default
from ..process_run import provision_runner
from .base import IPackageManager


class LinuxPackageManager(IPackageManager):
    """Speaks apt-format package names as its lingua franca.

    Args:
        runner: Runs the package commands; the provision runner on *console* when ``None``.
        console: The console the manager and its runner print through.
    """

    def __init__(self, runner: CommandRunner | None = None, *, console: Any = None) -> None:
        """Keep the console and the runner every package command goes through."""
        console = console_or_default(console, "LinuxPackageManager")
        super().__init__(console=console)
        self._runner = runner or provision_runner(console)

    def _drain(self, command: list[str], dry_run: bool, *, check: bool = False) -> int:
        """Run *command*, streaming its output through the console; return its exit code."""
        return self._runner.run_drained(command, None, dry_run=dry_run, check=check)

    @property
    def automates_gpu_sdk(self) -> bool:
        """Whether the GPU compute SDK is installed through this manager; False by default."""
        return False

    @property
    def automates_oneapi(self) -> bool:
        """Whether :meth:`install_oneapi` installs the oneAPI compiler; False by default."""
        return False

    def install_oneapi(self, dry_run: bool) -> bool:
        """Install the Intel oneAPI DPC++ compiler; False when this manager does not automate it."""
        return False

    def install_acpp_build_deps(self, llvm_version: str) -> tuple[str | None, str | None]:
        """Install the AdaptiveCpp build dependencies for LLVM *llvm_version*.

        Returns:
            ``(LLVM_DIR, clang_prefix)``; an empty ``LLVM_DIR`` makes cmake search its defaults.
        """
        self.install(self.translate_apt(
            ["clang", "llvm", "libboost-context-dev", "libboost-fiber-dev"]), dry_run=False)
        return ("", None)

    def translate_apt(self, apt_pkgs: list[str]) -> list[str]:
        """Convert apt-format package names to this manager's native names."""
        return apt_pkgs
