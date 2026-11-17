# system.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Operating-system facts and the bash call shared by the package managers and the GPU backends."""

from __future__ import annotations

from .default_console import console_or_default

import logging
import os
from pathlib import Path
from typing import Any, Callable

from sushicore.proc import CommandRunner
from sushicore.provision.process_run import provision_runner
from sushicore.moved_name import moved_attribute

_log = logging.getLogger(__name__)

#: The User-Agent header every installer download and release lookup sends.
USER_AGENT = "sushicore-installer"


def is_root() -> bool:
    """Return True when the current process already runs as root."""
    try:
        return os.geteuid() == 0  # type: ignore[attr-defined]
    except AttributeError:
        return False


def os_release(read_text: Callable[[], str] | None = None) -> dict[str, str]:
    """Parse /etc/os-release into a dict (empty off Linux or when unreadable).

    Args:
        read_text: Gives the file's text or raises ``OSError``; reads ``/etc/os-release`` when ``None``.
    """
    data: dict[str, str] = {}
    try:
        text = read_text() if read_text else Path("/etc/os-release").read_text(encoding="utf-8")
        for line in text.splitlines():
            if "=" in line and not line.startswith("#"):
                key, _, val = line.partition("=")
                data[key.strip()] = val.strip().strip('"')
    except FileNotFoundError:
        _log.debug("/etc/os-release is absent; no distribution field is reported")
    except OSError as error:
        _log.warning(
            "/etc/os-release was not read (%s: %s); no distribution field is reported",
            type(error).__name__,
            error,
        )
    return data


def run_bash(cmd: str, runner: CommandRunner | None, console: Any) -> int:
    """Run *cmd* through bash here, its output shown on *console*; return the exit code."""
    return (runner or provision_runner(console)).run(["bash", "-c", cmd], Path.cwd())


def sudo_bash(cmd: str, dry_run: bool, runner: CommandRunner | None = None, *,
              console: Any = None) -> bool:
    """Run *cmd* through bash and return whether it exited zero; a dry run always returns True.

    Args:
        runner: Runs bash, which echoes the command; the provision runner on *console* when
            ``None``.
        console: The console the command and its output are shown through.
    """
    console = console_or_default(console, "sudo_bash")
    if dry_run:
        console.command(cmd)
        console.info("(dry-run) not executed")
        return True
    return run_bash(cmd, runner, console) == 0

#: Each name that left this module and the module that holds it now.
K_MOVED = {"ensure_intel_oneapi_repo": "sushicore.provision.intel_oneapi_repo"}


def __getattr__(name: str) -> object:
    """Return a name that moved to another module, with a deprecation warning."""
    return moved_attribute(globals(), K_MOVED, name)
