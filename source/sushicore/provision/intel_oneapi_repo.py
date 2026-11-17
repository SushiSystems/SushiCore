# intel_oneapi_repo.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Configures the Intel oneAPI apt repository on Debian and Ubuntu."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from sushicore.proc import CommandRunner
from sushicore.provision.default_console import console_or_default
from sushicore.provision.system import is_root, run_bash

#: Where the Intel oneAPI apt repo keyring and source list are written.
K_ONEAPI_KEYRING = Path("/usr/share/keyrings/oneapi-archive-keyring.gpg")
K_ONEAPI_LIST = Path("/etc/apt/sources.list.d/oneAPI.list")
K_ONEAPI_KEY_URL = (
    "https://apt.repos.intel.com/intel-gpg-keys/GPG-PUB-KEY-INTEL-SW-PRODUCTS.PUB"
)


def ensure_intel_oneapi_repo(dry_run: bool, runner: CommandRunner | None = None, *,
                             console: Any = None, keyring: Path = K_ONEAPI_KEYRING,
                             source_list: Path = K_ONEAPI_LIST) -> bool:
    """Configure the Intel oneAPI apt repository on Debian/Ubuntu, skipping a configured one.

    Args:
        runner: Runs bash for each step; the provision runner on *console* when ``None``.
        console: The console the steps are shown through.
        keyring: The keyring file the repository is signed with.
        source_list: The apt source list that names the repository.
    """
    console = console_or_default(console, "ensure_intel_oneapi_repo")
    if keyring.is_file() and source_list.is_file():
        console.info("Intel oneAPI apt repository already configured.")
        return True
    sudo = "" if is_root() else "sudo "
    key_cmd = f"curl -fsSL {K_ONEAPI_KEY_URL} | {sudo}gpg --dearmor -o {keyring}"
    list_cmd = (
        f'echo "deb [signed-by={keyring}] '
        f'https://apt.repos.intel.com/oneapi all main" | {sudo}tee {source_list}'
    )
    if dry_run:
        console.command(key_cmd)
        console.command(list_cmd)
        console.info("(dry-run) not executed")
        return True
    for cmd in (key_cmd, list_cmd):
        if run_bash(cmd, runner, console) != 0:
            console.error("Failed to configure the Intel oneAPI apt repository "
                          "(need curl and gpg). Install oneAPI manually or skip it.")
            return False
    return True
