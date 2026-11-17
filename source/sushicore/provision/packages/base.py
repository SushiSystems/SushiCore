# base.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The contract a package manager implements."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ..default_console import console_or_default
from ..moved_name import moved_attribute


class IPackageManager(ABC):
    """Installs packages of one kind and reports availability."""

    name: str = "pkg"

    def __init__(self, *, console: Any = None) -> None:
        """Keep the console a manager prints through.

        Args:
            console: The console the manager reports through.
        """
        console = console_or_default(console, "IPackageManager")
        self._console = console

    @abstractmethod
    def available(self) -> bool:
        """Report whether the underlying tool is present on this machine."""

    @abstractmethod
    def is_installed(self, pkg: str) -> bool:
        """Report whether *pkg* is already installed, on a best-effort basis."""

    @abstractmethod
    def install(self, pkgs: list[str], dry_run: bool) -> bool:
        """Install the given packages.

        Returns:
            True on success.
        """

    def remove(self, pkgs: list[str], dry_run: bool) -> bool:
        """Remove the given packages, on a best-effort basis.

        Returns:
            True on success.
        """
        self._console.warn(f"{self.name}: remove not implemented, skipping.")
        return True

#: Each name that left this module and the module that holds it now.
K_MOVED = {
    "refresh_windows_path": "sushicore.provision.packages.windows_path",
    "K_WINDOWS_PATH_SEPARATOR": "sushicore.provision.packages.windows_path",
}


def __getattr__(name: str) -> object:
    """Return a name that moved to another module, with a deprecation warning."""
    return moved_attribute(globals(), K_MOVED, name)
