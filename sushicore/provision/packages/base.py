# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""The package-manager contract and the process helpers its implementations share."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from abc import ABC, abstractmethod

from .._output import console
from ..system import is_root


def _run(cmd: list[str], dry_run: bool, *, check: bool = False) -> int:
    """Run *cmd*, streaming its output through the console; return its exit code."""
    console.command(subprocess.list2cmdline(cmd))
    if dry_run:
        console.info("(dry-run) not executed")
        return 0
    process = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding="utf-8", errors="replace",
    )
    if process.stdout:
        for line in iter(process.stdout.readline, ""):
            console.console.print(line.rstrip("\n"), markup=False, highlight=False)
    process.wait()
    if check and process.returncode != 0:
        console.error(f"Command failed ({process.returncode}).")
    return process.returncode


def prime_sudo() -> None:
    """Prompt for the sudo password once, before any progress display starts."""
    if os.name == "nt" or is_root() or shutil.which("sudo") is None:
        return

    tty = None
    if not (sys.stdin and sys.stdin.isatty()):
        try:
            tty = open("/dev/tty", "r")
        except OSError:
            console.warn(
                "No terminal available for a sudo password prompt. If dependency "
                "installation fails, run the install command directly in a terminal, "
                "or pre-authorize with `sudo -v`."
            )
            return

    console.warn("Administrator (sudo) access needed — enter your password below.")
    try:
        subprocess.run(["sudo", "-p", "[sudo] password for %p: ", "-v"], stdin=tty)
    except OSError as exc:
        console.warn(f"Could not prime sudo credentials: {exc}")
    finally:
        if tty is not None:
            tty.close()


def refresh_windows_path() -> None:
    """Reload PATH from the registry into this process (Windows only, else no-op)."""
    if os.name != "nt":
        return
    try:
        import winreg
        parts: list[str] = []
        for root, sub in (
            (winreg.HKEY_LOCAL_MACHINE,
             r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"),
            (winreg.HKEY_CURRENT_USER, r"Environment"),
        ):
            try:
                key = winreg.OpenKey(root, sub)
                try:
                    val, _ = winreg.QueryValueEx(key, "Path")
                    parts.append(os.path.expandvars(str(val)))
                finally:
                    winreg.CloseKey(key)
            except FileNotFoundError:
                pass
        parts.append(os.environ.get("PATH", ""))
        seen: set[str] = set()
        out: list[str] = []
        for entry in os.pathsep.join(parts).split(os.pathsep):
            key_l = entry.lower()
            if entry and key_l not in seen:
                seen.add(key_l)
                out.append(entry)
        os.environ["PATH"] = os.pathsep.join(out)
    except Exception:
        pass


class IPackageManager(ABC):
    """Installs packages of one kind and reports availability."""

    name: str = "pkg"

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
        console.warn(f"{self.name}: remove not implemented, skipping.")
        return True
