# posix.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The POSIX host: Linux and the systems that follow its conventions."""

from __future__ import annotations

import logging
import os
import platform
from pathlib import Path
from typing import final

from sushicore.proc import CommandRunner, did_not_run

from .base import IHost

_log = logging.getLogger(__name__)


@final
class PosixHost(IHost):
    """Links with symlinks, locks with ``flock`` and reads ``lspci``."""

    def make_dir_link(self, link: Path, target: Path) -> None:
        """Create *link* as a symlink to *target*."""
        os.symlink(target.resolve(), link, target_is_directory=True)

    def remove_dir_link(self, path: Path) -> None:
        """Remove the symlink *path*."""
        path.unlink()

    def replace_dir_link(self, link: Path, target: Path) -> None:
        """Create the symlink beside *link* and rename it over, so a reader never sees it missing."""
        beside = link.with_name(link.name + ".new")
        if beside.is_symlink():
            beside.unlink()
        os.symlink(target.resolve(), beside, target_is_directory=True)
        os.replace(beside, link)

    def is_junction(self, path: Path) -> bool:
        """False; there are no junctions."""
        return False

    def try_lock(self, fd: int) -> bool:
        """Take ``flock`` on *fd* without blocking."""
        import fcntl
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            return False
        return True

    def unlock(self, fd: int) -> None:
        """Release the ``flock`` on *fd*."""
        import fcntl
        fcntl.flock(fd, fcntl.LOCK_UN)

    def registry_paths(self) -> list[str] | None:
        """None; there is no registry."""
        return None

    def display_adapters(self, runner: CommandRunner) -> str:
        """Return the lower-case display-controller lines ``lspci`` reports, or ''."""
        code, out, err = runner.capture(["lspci"], timeout=10)
        if did_not_run("lspci", code, err):
            _log.warning("lspci did not run (%s); no display adapter is reported", err)
            return ""
        return "\n".join(
            ln for ln in out.lower().splitlines()
            if "vga compatible controller" in ln or "3d controller" in ln
            or "display controller" in ln
        )

    def long_path(self, path: Path) -> Path:
        """Return *path* unchanged; there is no path-length limit to lift."""
        return path

    @property
    def nvcc_name(self) -> str:
        """``nvcc``."""
        return "nvcc"

    @property
    def cuda_platform_key(self) -> str:
        """``linux-sbsa`` on ARM64, ``linux-x86_64`` otherwise."""
        machine = platform.machine().lower()
        return "linux-sbsa" if machine in ("aarch64", "arm64") else "linux-x86_64"

    @property
    def searches_system_prefixes(self) -> bool:
        """True."""
        return True

    @property
    def hosts_visual_studio(self) -> bool:
        """False."""
        return False

    @property
    def keeps_environment_in_registry(self) -> bool:
        """False; the variables live in a shell profile."""
        return False
