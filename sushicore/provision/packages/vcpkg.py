# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""The vcpkg package manager for C++ library ports."""

from __future__ import annotations

import shutil
import subprocess
import typing
from pathlib import Path

from .. import home
from .._output import console
from .base import IPackageManager, _run

if typing.TYPE_CHECKING:
    from ..config import ProvisionConfig


def _port_name(pkg: str) -> str:
    """Return a vcpkg port reference without the feature list it may carry."""
    return pkg.split("[", 1)[0]


class VcpkgManager(IPackageManager):
    """Vcpkg for C++ library ports (hwloc, gtest, pkgconf, …)."""

    name = "vcpkg"

    def __init__(self, cfg: "ProvisionConfig") -> None:
        """Store *cfg* and resolve the triplet to install ports for."""
        self._cfg = cfg
        self._triplet = cfg.vcpkg_triplet or (
            "x64-windows" if cfg.platform == "windows" else "x64-linux")

    def _root(self) -> Path:
        """Return the configured vcpkg root, or the dependency root's default."""
        root = self._cfg.expand(self._cfg.vcpkg_root) if self._cfg.vcpkg_root else ""
        if root:
            return Path(root)
        return home.vcpkg_dir()

    def _exe(self) -> Path:
        """Return the path of the vcpkg executable under this manager's root."""
        name = "vcpkg.exe" if self._cfg.platform == "windows" else "vcpkg"
        return self._root() / name

    def available(self) -> bool:
        """Report whether the vcpkg executable exists, locally or on PATH."""
        return self._exe().is_file() or shutil.which("vcpkg") is not None

    def ensure_bootstrapped(self, dry_run: bool) -> bool:
        """Clone and bootstrap vcpkg into its root if not already present."""
        root = self._root()
        if self._exe().is_file():
            return True
        console.info(f"vcpkg not found; bootstrapping into {root} ...")
        if not (root / ".git").is_dir():
            if root.exists():
                console.info(f"Removing stale directory {root} before cloning ...")
                if not dry_run:
                    shutil.rmtree(root)
            rc = _run(["git", "clone", "https://github.com/microsoft/vcpkg.git",
                       str(root)], dry_run, check=True)
            if rc != 0 and not dry_run:
                return False
        if self._cfg.platform == "windows":
            bootstrap = root / "bootstrap-vcpkg.bat"
            rc = _run(["cmd", "/c", str(bootstrap), "-disableMetrics"], dry_run, check=True)
        else:
            bootstrap = root / "bootstrap-vcpkg.sh"
            if not dry_run:
                bootstrap.chmod(bootstrap.stat().st_mode | 0o111)
            rc = _run([str(bootstrap), "-disableMetrics"], dry_run, check=True)
        return rc == 0 or dry_run

    def is_installed(self, pkg: str) -> bool:
        """Report whether *pkg*'s port is listed as installed for this triplet."""
        if not self.available():
            return False
        exe = self._exe() if self._exe().is_file() else Path("vcpkg")
        try:
            result = subprocess.run(
                [str(exe), "list", "--triplet", self._triplet],
                capture_output=True, text=True,
            )
        except OSError:
            return False
        return result.returncode == 0 and _port_name(pkg).lower() in result.stdout.lower()

    def install(self, pkgs: list[str], dry_run: bool) -> bool:
        """Bootstrap vcpkg if needed, then install *pkgs* for this triplet."""
        if not pkgs:
            return True
        if not self.ensure_bootstrapped(dry_run):
            console.error("vcpkg bootstrap failed.")
            return False
        exe = self._exe()
        ports = [f"{p}:{self._triplet}" for p in pkgs]
        rc = _run([str(exe), "install", *ports], dry_run, check=True)
        return rc == 0

    def remove(self, pkgs: list[str], dry_run: bool) -> bool:
        """Remove *pkgs* for this triplet, when the vcpkg executable exists."""
        if not pkgs:
            return True
        exe = self._exe()
        if not exe.is_file():
            console.warn("vcpkg not found; skipping port removal.")
            return True
        ports = [f"{p}:{self._triplet}" for p in pkgs]
        rc = _run([str(exe), "remove", *ports], dry_run, check=True)
        return rc == 0
