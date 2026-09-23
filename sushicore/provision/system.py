# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Operating-system helpers shared by the package managers and the GPU backends."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from sushicore.provision._output import console

#: Where the Intel oneAPI apt repo keyring and source list are written.
_ONEAPI_KEYRING = Path("/usr/share/keyrings/oneapi-archive-keyring.gpg")
_ONEAPI_LIST = Path("/etc/apt/sources.list.d/oneAPI.list")
_ONEAPI_KEY_URL = (
    "https://apt.repos.intel.com/intel-gpg-keys/GPG-PUB-KEY-INTEL-SW-PRODUCTS.PUB"
)


def is_root() -> bool:
    """Return True when the current process already runs as root."""
    try:
        return os.geteuid() == 0  # type: ignore[attr-defined]
    except AttributeError:
        return False


def os_release() -> dict[str, str]:
    """Parse /etc/os-release into a dict (empty off Linux or when unreadable)."""
    data: dict[str, str] = {}
    try:
        for line in Path("/etc/os-release").read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.startswith("#"):
                key, _, val = line.partition("=")
                data[key.strip()] = val.strip().strip('"')
    except OSError:
        pass
    return data


def sudo_bash(cmd: str, dry_run: bool) -> bool:
    """Run *cmd* through bash and return whether it exited zero; a dry run always returns True."""
    console.command(cmd)
    if dry_run:
        console.info("(dry-run) not executed")
        return True
    return subprocess.run(["bash", "-c", cmd]).returncode == 0


def ensure_intel_oneapi_repo(dry_run: bool) -> bool:
    """Configure the Intel oneAPI apt repository (Debian/Ubuntu only); skips when already configured."""
    if _ONEAPI_KEYRING.is_file() and _ONEAPI_LIST.is_file():
        console.info("Intel oneAPI apt repository already configured.")
        return True
    sudo = "" if is_root() else "sudo "
    key_cmd = f"curl -fsSL {_ONEAPI_KEY_URL} | {sudo}gpg --dearmor -o {_ONEAPI_KEYRING}"
    list_cmd = (
        f'echo "deb [signed-by={_ONEAPI_KEYRING}] '
        f'https://apt.repos.intel.com/oneapi all main" | {sudo}tee {_ONEAPI_LIST}'
    )
    console.command(key_cmd)
    console.command(list_cmd)
    if dry_run:
        console.info("(dry-run) not executed")
        return True
    for cmd in (key_cmd, list_cmd):
        if subprocess.run(["bash", "-c", cmd]).returncode != 0:
            console.error("Failed to configure the Intel oneAPI apt repository "
                          "(need curl and gpg). Install oneAPI manually or skip it.")
            return False
    return True
