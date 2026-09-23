# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""The Windows winget package manager."""

from __future__ import annotations

import shutil
import subprocess

from .base import IPackageManager, _run


class WingetManager(IPackageManager):
    """Windows winget for system toolchain packages."""

    name = "winget"

    def available(self) -> bool:
        """Report whether ``winget`` is on PATH."""
        return shutil.which("winget") is not None

    def is_installed(self, pkg: str) -> bool:
        """Report whether winget lists *pkg* as installed."""
        try:
            result = subprocess.run(
                ["winget", "list", "--id", pkg, "-e"],
                capture_output=True, text=True,
            )
        except OSError:
            return False
        return result.returncode == 0 and pkg.lower() in result.stdout.lower()

    def install(self, pkgs: list[str], dry_run: bool) -> bool:
        """Install each of *pkgs* through ``winget install``."""
        ok = True
        for pkg in pkgs:
            rc = _run(
                ["winget", "install", "--id", pkg, "-e",
                 "--accept-package-agreements", "--accept-source-agreements",
                 "--silent"],
                dry_run, check=True,
            )
            ok = ok and rc == 0
        return ok

    def remove(self, pkgs: list[str], dry_run: bool) -> bool:
        """Uninstall each of *pkgs* through ``winget uninstall``."""
        ok = True
        for pkg in pkgs:
            rc = _run(
                ["winget", "uninstall", "--id", pkg, "-e", "--silent"],
                dry_run,
            )
            ok = ok and rc == 0
        return ok
