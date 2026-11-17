# base.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The package-manager contract and the PATH helper its implementations share."""

from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from typing import Callable, MutableMapping

from .._output import console

_log = logging.getLogger(__name__)

K_WINDOWS_PATH_SEPARATOR = ";"


def _registry_paths() -> list[str]:
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


def refresh_windows_path(read_paths: Callable[[], list[str]] | None = None,
                         environ: MutableMapping[str, str] | None = None) -> None:
    """Reload PATH from the registry into this process (Windows only, else no-op).

    Args:
        read_paths: Gives the registry's ``Path`` values or raises ``OSError``; given, it is
            read on any platform. The registry on Windows when ``None``.
        environ: The environment to update; the process's when ``None``.
    """
    if os.name != "nt" and read_paths is None:
        return
    env = os.environ if environ is None else environ
    try:
        parts = (read_paths or _registry_paths)()
        parts.append(env.get("PATH", ""))
        seen: set[str] = set()
        out: list[str] = []
        for entry in K_WINDOWS_PATH_SEPARATOR.join(parts).split(K_WINDOWS_PATH_SEPARATOR):
            key_l = entry.lower()
            if entry and key_l not in seen:
                seen.add(key_l)
                out.append(entry)
        env["PATH"] = K_WINDOWS_PATH_SEPARATOR.join(out)
    except OSError as error:
        _log.warning(
            "PATH was not reloaded from the registry (%s: %s); this process keeps its old PATH",
            type(error).__name__,
            error,
        )


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
