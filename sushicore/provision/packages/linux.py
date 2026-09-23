# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Package managers for the Linux distributions provision supports."""

from __future__ import annotations

import shutil
import subprocess

from .._output import console
from ..system import is_root
from .base import IPackageManager, _run

_APT_TO_DNF: dict[str, list[str]] = {
    "build-essential":     ["gcc", "gcc-c++", "make"],
    "ninja-build":         ["ninja-build"],
    "libhwloc-dev":        ["hwloc-devel"],
    "libgtest-dev":        ["gtest-devel"],
    "ocl-icd-opencl-dev":  ["ocl-icd"],
    "ocl-icd-libopencl1":  [],
    "pkg-config":          ["pkgconf"],
}

_APT_TO_PACMAN: dict[str, list[str]] = {
    "build-essential":     ["base-devel"],
    "ninja-build":         ["ninja"],
    "libhwloc-dev":        ["hwloc"],
    "libgtest-dev":        ["gtest"],
    "ocl-icd-opencl-dev":  ["ocl-icd"],
    "ocl-icd-libopencl1":  [],
    "pkg-config":          ["pkgconf"],
}

_APT_TO_ZYPPER: dict[str, list[str]] = {
    "build-essential":     ["gcc", "gcc-c++", "make"],
    "ninja-build":         ["ninja"],
    "libhwloc-dev":        ["hwloc-devel"],
    "libgtest-dev":        ["gtest"],
    "ocl-icd-opencl-dev":  ["ocl-icd"],
    "ocl-icd-libopencl1":  [],
    "pkg-config":          ["pkgconf"],
}


def _translate(apt_pkgs: list[str], table: dict[str, list[str]]) -> list[str]:
    """Map each apt-format package name in *apt_pkgs* through *table*."""
    out: list[str] = []
    for pkg in apt_pkgs:
        out.extend(table.get(pkg, [pkg]))
    return out


class LinuxPackageManager(IPackageManager):
    """Speaks apt-format package names as its lingua franca."""

    def translate_apt(self, apt_pkgs: list[str]) -> list[str]:
        """Convert apt-format package names to this manager's native names."""
        return apt_pkgs


class AptManager(LinuxPackageManager):
    """Installs Debian/Ubuntu packages through apt-get."""

    name = "apt"

    def available(self) -> bool:
        """Report whether ``apt-get`` is on PATH."""
        return shutil.which("apt-get") is not None

    def is_installed(self, pkg: str) -> bool:
        """Report whether dpkg lists *pkg* as installed."""
        try:
            result = subprocess.run(
                ["dpkg-query", "-W", "-f=${Status}", pkg],
                capture_output=True, text=True,
            )
        except OSError:
            return False
        return result.returncode == 0 and "install ok installed" in result.stdout

    def install(self, pkgs: list[str], dry_run: bool) -> bool:
        """Update the apt cache, then install *pkgs*."""
        if not pkgs:
            return True
        sudo = [] if is_root() else ["sudo"]
        if _run([*sudo, "apt-get", "update"], dry_run) != 0 and not dry_run:
            console.warn("apt-get update failed; continuing anyway.")
        rc = _run([*sudo, "apt-get", "install", "-y", *pkgs], dry_run, check=True)
        return rc == 0

    def remove(self, pkgs: list[str], dry_run: bool) -> bool:
        """Remove *pkgs* through ``apt-get remove``."""
        if not pkgs:
            return True
        sudo = [] if is_root() else ["sudo"]
        rc = _run([*sudo, "apt-get", "remove", "-y", *pkgs], dry_run, check=True)
        return rc == 0


class DnfManager(LinuxPackageManager):
    """Installs Fedora/RHEL packages through dnf."""

    name = "dnf"

    def available(self) -> bool:
        """Report whether ``dnf`` is on PATH."""
        return shutil.which("dnf") is not None

    def is_installed(self, pkg: str) -> bool:
        """Report whether rpm lists *pkg* as installed."""
        try:
            result = subprocess.run(
                ["rpm", "-q", pkg], capture_output=True, text=True,
            )
            return result.returncode == 0
        except OSError:
            return False

    def translate_apt(self, apt_pkgs: list[str]) -> list[str]:
        """Convert apt-format package names to dnf-native names."""
        return _translate(apt_pkgs, _APT_TO_DNF)

    def install(self, pkgs: list[str], dry_run: bool) -> bool:
        """Install *pkgs* through ``dnf install``."""
        if not pkgs:
            return True
        sudo = [] if is_root() else ["sudo"]
        rc = _run([*sudo, "dnf", "install", "-y", *pkgs], dry_run, check=True)
        return rc == 0

    def remove(self, pkgs: list[str], dry_run: bool) -> bool:
        """Remove *pkgs* through ``dnf remove``."""
        if not pkgs:
            return True
        sudo = [] if is_root() else ["sudo"]
        rc = _run([*sudo, "dnf", "remove", "-y", *pkgs], dry_run, check=True)
        return rc == 0


class YumManager(LinuxPackageManager):
    """Installs legacy RHEL/CentOS packages through yum."""

    name = "yum"

    def available(self) -> bool:
        """Report whether ``yum`` is on PATH and ``dnf`` is not."""
        return shutil.which("yum") is not None and shutil.which("dnf") is None

    def is_installed(self, pkg: str) -> bool:
        """Report whether rpm lists *pkg* as installed."""
        try:
            result = subprocess.run(
                ["rpm", "-q", pkg], capture_output=True, text=True,
            )
            return result.returncode == 0
        except OSError:
            return False

    def translate_apt(self, apt_pkgs: list[str]) -> list[str]:
        """Convert apt-format package names to dnf/yum-native names."""
        return _translate(apt_pkgs, _APT_TO_DNF)

    def install(self, pkgs: list[str], dry_run: bool) -> bool:
        """Install *pkgs* through ``yum install``."""
        if not pkgs:
            return True
        sudo = [] if is_root() else ["sudo"]
        rc = _run([*sudo, "yum", "install", "-y", *pkgs], dry_run, check=True)
        return rc == 0

    def remove(self, pkgs: list[str], dry_run: bool) -> bool:
        """Remove *pkgs* through ``yum remove``."""
        if not pkgs:
            return True
        sudo = [] if is_root() else ["sudo"]
        rc = _run([*sudo, "yum", "remove", "-y", *pkgs], dry_run, check=True)
        return rc == 0


class PacmanManager(LinuxPackageManager):
    """Installs Arch Linux packages through pacman."""

    name = "pacman"

    def available(self) -> bool:
        """Report whether ``pacman`` is on PATH."""
        return shutil.which("pacman") is not None

    def is_installed(self, pkg: str) -> bool:
        """Report whether pacman lists *pkg* as installed."""
        try:
            result = subprocess.run(
                ["pacman", "-Q", pkg], capture_output=True, text=True,
            )
            return result.returncode == 0
        except OSError:
            return False

    def translate_apt(self, apt_pkgs: list[str]) -> list[str]:
        """Convert apt-format package names to pacman-native names."""
        return _translate(apt_pkgs, _APT_TO_PACMAN)

    def install(self, pkgs: list[str], dry_run: bool) -> bool:
        """Install *pkgs* through ``pacman -Sy``."""
        if not pkgs:
            return True
        sudo = [] if is_root() else ["sudo"]
        rc = _run([*sudo, "pacman", "-Sy", "--noconfirm", *pkgs], dry_run, check=True)
        return rc == 0

    def remove(self, pkgs: list[str], dry_run: bool) -> bool:
        """Remove *pkgs* through ``pacman -R``."""
        if not pkgs:
            return True
        sudo = [] if is_root() else ["sudo"]
        rc = _run([*sudo, "pacman", "-R", "--noconfirm", *pkgs], dry_run, check=True)
        return rc == 0


class ZypperManager(LinuxPackageManager):
    """Installs openSUSE packages through zypper."""

    name = "zypper"

    def available(self) -> bool:
        """Report whether ``zypper`` is on PATH."""
        return shutil.which("zypper") is not None

    def is_installed(self, pkg: str) -> bool:
        """Report whether rpm lists *pkg* as installed."""
        try:
            result = subprocess.run(
                ["rpm", "-q", pkg], capture_output=True, text=True,
            )
            return result.returncode == 0
        except OSError:
            return False

    def translate_apt(self, apt_pkgs: list[str]) -> list[str]:
        """Convert apt-format package names to zypper-native names."""
        return _translate(apt_pkgs, _APT_TO_ZYPPER)

    def install(self, pkgs: list[str], dry_run: bool) -> bool:
        """Install *pkgs* through ``zypper install``."""
        if not pkgs:
            return True
        sudo = [] if is_root() else ["sudo"]
        rc = _run([*sudo, "zypper", "install", "-y", *pkgs], dry_run, check=True)
        return rc == 0

    def remove(self, pkgs: list[str], dry_run: bool) -> bool:
        """Remove *pkgs* through ``zypper remove``."""
        if not pkgs:
            return True
        sudo = [] if is_root() else ["sudo"]
        rc = _run([*sudo, "zypper", "remove", "-y", *pkgs], dry_run, check=True)
        return rc == 0
