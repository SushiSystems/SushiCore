# vcpkg.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The vcpkg package manager for C++ library ports."""

from __future__ import annotations

import shutil
import typing
from pathlib import Path

from sushicore.proc import CommandRunner

from .. import home
from ..process_run import provision_runner
from ..target import target_of
from .base import IPackageManager

if typing.TYPE_CHECKING:
    from ..config import ProvisionConfig


def _port_name(pkg: str) -> str:
    """Return a vcpkg port reference without the feature list it may carry."""
    return pkg.split("[", 1)[0]


class VcpkgManager(IPackageManager):
    """Installs C++ library ports (hwloc, gtest, pkgconf, …) through vcpkg."""

    name = "vcpkg"

    def __init__(self, cfg: "ProvisionConfig", runner: CommandRunner | None = None, *,
                 console: typing.Any) -> None:
        """Store *cfg*, the runner of the vcpkg commands, and resolve the triplet to install for.

        Args:
            cfg: The provision configuration.
            runner: Runs the git, bootstrap and vcpkg commands; the provision runner on *console*
                when ``None``.
            console: The console the manager and its runner print through.
        """
        super().__init__(console=console)
        self._cfg = cfg
        self._runner = runner or provision_runner(console)
        self._target = target_of(cfg)
        self._triplet = cfg.vcpkg_triplet or self._target.vcpkg_triplet

    def _drain(self, command: list[str], dry_run: bool) -> int:
        """Run *command*, streaming its output through the console; report a failure once."""
        return self._runner.run_drained(command, None, dry_run=dry_run, check=True)

    def _root(self) -> Path:
        """Return the configured vcpkg root, else the tree a dependency root already holds."""
        root = self._cfg.expand(self._cfg.vcpkg_root) if self._cfg.vcpkg_root else ""
        if root:
            return Path(root)
        return home.found_vcpkg_dir()

    def _exe(self) -> Path:
        """Return the path of the vcpkg executable under this manager's root."""
        return self._root() / self._target.vcpkg_executable

    def available(self) -> bool:
        """Report whether the vcpkg executable exists, locally or on PATH."""
        return self._exe().is_file() or shutil.which("vcpkg") is not None

    def ensure_bootstrapped(self, dry_run: bool) -> bool:
        """Clone and bootstrap vcpkg into its root if not already present."""
        root = self._root()
        if self._exe().is_file():
            return True
        self._console.info(f"vcpkg not found; bootstrapping into {root} ...")
        if not (root / ".git").is_dir():
            if root.exists():
                self._console.info(f"Removing stale directory {root} before cloning ...")
                if not dry_run:
                    shutil.rmtree(root)
            rc = self._drain(["git", "clone", "https://github.com/microsoft/vcpkg.git",
                              str(root)], dry_run)
            if rc != 0 and not dry_run:
                return False
        rc = self._target.bootstrap_vcpkg(root, self._drain, dry_run)
        return rc == 0 or dry_run

    def is_installed(self, pkg: str) -> bool:
        """Report whether *pkg*'s port is listed as installed for this triplet."""
        if not self.available():
            return False
        exe = self._exe() if self._exe().is_file() else Path("vcpkg")
        try:
            code, output, _error = self._runner.capture(
                [str(exe), "list", "--triplet", self._triplet])
        except OSError:
            return False
        return code == 0 and _port_name(pkg).lower() in output.lower()

    def install(self, pkgs: list[str], dry_run: bool) -> bool:
        """Bootstrap vcpkg if needed, then install *pkgs* for this triplet."""
        if not pkgs:
            return True
        if not self.ensure_bootstrapped(dry_run):
            self._console.error("vcpkg bootstrap failed.")
            return False
        exe = self._exe()
        ports = [f"{p}:{self._triplet}" for p in pkgs]
        rc = self._drain([str(exe), "install", *ports], dry_run)
        return rc == 0

    def remove(self, pkgs: list[str], dry_run: bool) -> bool:
        """Remove *pkgs* for this triplet, when the vcpkg executable exists."""
        if not pkgs:
            return True
        exe = self._exe()
        if not exe.is_file():
            self._console.warn("vcpkg not found; skipping port removal.")
            return True
        ports = [f"{p}:{self._triplet}" for p in pkgs]
        rc = self._drain([str(exe), "remove", *ports], dry_run)
        return rc == 0
