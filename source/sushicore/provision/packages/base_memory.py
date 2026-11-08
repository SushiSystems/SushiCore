# base_memory.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""A Linux package manager that holds its packages in memory and runs no command."""

from __future__ import annotations

from typing import Iterable

from .linux import LinuxPackageManager


class InMemoryLinuxPackageManager(LinuxPackageManager):
    """Keeps the packages it was told are installed and records each install and removal.

    Args:
        name: The manager's name, such as ``apt``.
        installed: Packages installed before the test begins.
        is_available: Whether the manager reports itself present.
        succeeds: Whether an install or a removal reports success.
    """

    def __init__(self, name: str = "apt", installed: Iterable[str] = (),
                 is_available: bool = True, succeeds: bool = True) -> None:
        """Store the manager's name, its held packages and how it answers."""
        self.name = name
        self.held = set(installed)
        self.installs: list[list[str]] = []
        self.removals: list[list[str]] = []
        self._available = is_available
        self._succeeds = succeeds

    def available(self) -> bool:
        """Report whether the manager was made present."""
        return self._available

    def is_installed(self, pkg: str) -> bool:
        """Report whether *pkg* is held."""
        return pkg in self.held

    def install(self, pkgs: list[str], dry_run: bool) -> bool:
        """Record the install and hold *pkgs* unless it is a dry run; report the scripted result."""
        self.installs.append(list(pkgs))
        if self._succeeds and not dry_run:
            self.held.update(pkgs)
        return self._succeeds

    def remove(self, pkgs: list[str], dry_run: bool) -> bool:
        """Record the removal and drop *pkgs* unless it is a dry run; report the scripted result."""
        self.removals.append(list(pkgs))
        if self._succeeds and not dry_run:
            self.held.difference_update(pkgs)
        return self._succeeds
