# windows.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The Windows host."""

from __future__ import annotations

import logging
import os
import stat
from pathlib import Path
from typing import final

from sushicore.proc import CommandRunner, did_not_run

from .base import IHost

_log = logging.getLogger(__name__)

#: Byte offset `msvcrt.locking` locks, separate from the PID text at offset 0.
_LOCK_BYTE = 1 << 20

#: The prefix that puts a Windows path in its extended-length form.
_EXTENDED_PREFIX = "\\\\?\\"


@final
class WindowsHost(IHost):
    """Links with junctions, locks with ``msvcrt`` and reads the registry."""

    def make_dir_link(self, link: Path, target: Path) -> None:
        """Create *link* as a junction to *target*."""
        import _winapi
        _winapi.CreateJunction(str(target.resolve()), str(link))

    def remove_dir_link(self, path: Path) -> None:
        """Remove the junction *path*."""
        os.rmdir(path)

    def replace_dir_link(self, link: Path, target: Path) -> None:
        """Delete the junction at *link*, when there is one, and create it again."""
        if link.is_symlink() or self.is_junction(link):
            self.remove_dir_link(link)
        self.make_dir_link(link, target)

    def is_junction(self, path: Path) -> bool:
        """Report whether *path* is a junction, read from its reparse tag."""
        try:
            tag = os.lstat(path).st_reparse_tag
        except OSError:
            return False
        return tag == stat.IO_REPARSE_TAG_MOUNT_POINT

    def try_lock(self, fd: int) -> bool:
        """Lock one byte of *fd* without blocking."""
        import msvcrt
        try:
            os.lseek(fd, _LOCK_BYTE, os.SEEK_SET)
            msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
        except OSError:
            return False
        return True

    def unlock(self, fd: int) -> None:
        """Unlock the byte :meth:`try_lock` locked."""
        import msvcrt
        os.lseek(fd, _LOCK_BYTE, os.SEEK_SET)
        msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)

    def registry_paths(self) -> list[str] | None:
        """Return the machine and the user ``Path`` values of the registry, variables expanded.

        Raises:
            OSError: The registry may not be read.
        """
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
                _log.debug("registry key %s has no Path value; skipped", sub)
        return parts

    def display_adapters(self, runner: CommandRunner) -> str:
        """Return the lower-case names of the video controllers Windows reports, or ''."""
        cmd = ["powershell", "-NoProfile", "-NonInteractive", "-Command",
               "Get-CimInstance Win32_VideoController | ForEach-Object { $_.Name }"]
        code, out, err = runner.capture(cmd, timeout=30)
        if did_not_run(cmd[0], code, err):
            _log.warning(
                "the Win32_VideoController query did not run (%s); no display adapter is reported",
                err)
            return ""
        return out.lower()

    def long_path(self, path: Path) -> Path:
        """Return *path* in the extended-length form, which lifts the 260-character limit."""
        text = str(path.resolve())
        return Path(text if text.startswith(_EXTENDED_PREFIX) else _EXTENDED_PREFIX + text)

    @property
    def nvcc_name(self) -> str:
        """``nvcc.exe``."""
        return "nvcc.exe"

    @property
    def cuda_platform_key(self) -> str:
        """``windows-x86_64``."""
        return "windows-x86_64"

    @property
    def searches_system_prefixes(self) -> bool:
        """False; Windows toolkits are found through PATH and the environment."""
        return False

    @property
    def hosts_visual_studio(self) -> bool:
        """True."""
        return True

    @property
    def keeps_environment_in_registry(self) -> bool:
        """True."""
        return True
