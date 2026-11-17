# pacman_manager.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Installs Arch Linux packages through pacman."""

from __future__ import annotations

import shutil
from typing import final

from ..system import is_root
from .apt_names import K_APT_TO_PACMAN, translate_names
from .linux_manager import LinuxPackageManager


@final
class PacmanManager(LinuxPackageManager):
    """Installs Arch Linux packages through pacman."""

    name = "pacman"

    def available(self) -> bool:
        """Report whether ``pacman`` is on PATH."""
        return shutil.which("pacman") is not None

    def is_installed(self, pkg: str) -> bool:
        """Report whether pacman lists *pkg* as installed."""
        try:
            code = self._runner.capture(["pacman", "-Q", pkg])[0]
            return code == 0
        except OSError:
            return False

    def translate_apt(self, apt_pkgs: list[str]) -> list[str]:
        """Convert apt-format package names to pacman-native names."""
        return translate_names(apt_pkgs, K_APT_TO_PACMAN)

    def install(self, pkgs: list[str], dry_run: bool) -> bool:
        """Install *pkgs* through ``pacman -Sy``."""
        if not pkgs:
            return True
        sudo = [] if is_root() else ["sudo"]
        rc = self._drain([*sudo, "pacman", "-Sy", "--noconfirm", *pkgs], dry_run, check=True)
        return rc == 0

    def remove(self, pkgs: list[str], dry_run: bool) -> bool:
        """Remove *pkgs* through ``pacman -R``."""
        if not pkgs:
            return True
        sudo = [] if is_root() else ["sudo"]
        rc = self._drain([*sudo, "pacman", "-R", "--noconfirm", *pkgs], dry_run, check=True)
        return rc == 0
