# windows_path.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Reloads this process's PATH from the Windows registry after an installer changed it."""

from __future__ import annotations

import logging
import os
from typing import Callable, MutableMapping

from ..host import current_host

_log = logging.getLogger(__name__)

K_WINDOWS_PATH_SEPARATOR = ";"


def refresh_windows_path(read_paths: Callable[[], list[str]] | None = None,
                         environ: MutableMapping[str, str] | None = None) -> None:
    """Reload PATH from the registry into this process (Windows only, else no-op).

    Args:
        read_paths: Gives the registry's ``Path`` values or raises ``OSError``; given, it is
            read on any platform. The running host's registry when ``None``.
        environ: The environment to update; the process's when ``None``.
    """
    env = os.environ if environ is None else environ
    try:
        parts = read_paths() if read_paths is not None else current_host().registry_paths()
        if parts is None:
            return
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
