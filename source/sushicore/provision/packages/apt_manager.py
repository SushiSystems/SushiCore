# apt_manager.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Installs Debian and Ubuntu packages through apt-get."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import final

from ..intel_oneapi_repo import ensure_intel_oneapi_repo
from ..system import is_root
from .linux_manager import LinuxPackageManager


@final
class AptManager(LinuxPackageManager):
    """Installs Debian/Ubuntu packages through apt-get."""

    name = "apt"

    @property
    def automates_gpu_sdk(self) -> bool:
        """True; the GPU SDK installs through apt."""
        return True

    @property
    def automates_oneapi(self) -> bool:
        """True; the Intel apt repository is configured by :meth:`install_oneapi`."""
        return True

    def install_oneapi(self, dry_run: bool) -> bool:
        """Configure the Intel apt repository, then install ``intel-oneapi-compiler-dpcpp-cpp``."""
        return (ensure_intel_oneapi_repo(dry_run, console=self._console)
                and self.install(["intel-oneapi-compiler-dpcpp-cpp"], dry_run))

    def install_acpp_build_deps(self, llvm_version: str) -> tuple[str | None, str | None]:
        """Install the versioned LLVM packages; return their cmake folder when it exists."""
        self.install([
            f"clang-{llvm_version}", f"llvm-{llvm_version}-dev",
            f"libclang-{llvm_version}-dev", f"lld-{llvm_version}",
            "libboost-context-dev", "libboost-fiber-dev",
        ], dry_run=False)
        llvm_dir = f"/usr/lib/llvm-{llvm_version}/lib/cmake/llvm"
        return (llvm_dir if Path(llvm_dir).is_dir() else None, f"/usr/lib/llvm-{llvm_version}")

    def available(self) -> bool:
        """Report whether ``apt-get`` is on PATH."""
        return shutil.which("apt-get") is not None

    def is_installed(self, pkg: str) -> bool:
        """Report whether dpkg lists *pkg* as installed."""
        try:
            code, output, _error = self._runner.capture(
                ["dpkg-query", "-W", "-f=${Status}", pkg])
        except OSError:
            return False
        return code == 0 and "install ok installed" in output

    def install(self, pkgs: list[str], dry_run: bool) -> bool:
        """Update the apt cache, then install *pkgs*."""
        if not pkgs:
            return True
        sudo = [] if is_root() else ["sudo"]
        if self._drain([*sudo, "apt-get", "update"], dry_run) != 0 and not dry_run:
            self._console.warn("apt-get update failed; continuing anyway.")
        rc = self._drain([*sudo, "apt-get", "install", "-y", *pkgs], dry_run, check=True)
        return rc == 0

    def remove(self, pkgs: list[str], dry_run: bool) -> bool:
        """Remove *pkgs* through ``apt-get remove``."""
        if not pkgs:
            return True
        sudo = [] if is_root() else ["sudo"]
        rc = self._drain([*sudo, "apt-get", "remove", "-y", *pkgs], dry_run, check=True)
        return rc == 0
