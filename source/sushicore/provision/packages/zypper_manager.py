# zypper_manager.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Installs openSUSE packages through zypper."""

from __future__ import annotations

import shutil

from ..system import is_root
from .apt_names import K_APT_TO_ZYPPER, translate_names
from .linux_manager import LinuxPackageManager


class ZypperManager(LinuxPackageManager):
    """Installs openSUSE packages through zypper."""

    name = "zypper"

    def available(self) -> bool:
        """Report whether ``zypper`` is on PATH."""
        return shutil.which("zypper") is not None

    def is_installed(self, pkg: str) -> bool:
        """Report whether rpm lists *pkg* as installed."""
        try:
            code = self._runner.capture(["rpm", "-q", pkg])[0]
            return code == 0
        except OSError:
            return False

    def translate_apt(self, apt_pkgs: list[str]) -> list[str]:
        """Convert apt-format package names to zypper-native names."""
        return translate_names(apt_pkgs, K_APT_TO_ZYPPER)

    def install(self, pkgs: list[str], dry_run: bool) -> bool:
        """Install *pkgs* through ``zypper install``."""
        if not pkgs:
            return True
        sudo = [] if is_root() else ["sudo"]
        rc = self._drain([*sudo, "zypper", "install", "-y", *pkgs], dry_run, check=True)
        return rc == 0

    def remove(self, pkgs: list[str], dry_run: bool) -> bool:
        """Remove *pkgs* through ``zypper remove``."""
        if not pkgs:
            return True
        sudo = [] if is_root() else ["sudo"]
        rc = self._drain([*sudo, "zypper", "remove", "-y", *pkgs], dry_run, check=True)
        return rc == 0
