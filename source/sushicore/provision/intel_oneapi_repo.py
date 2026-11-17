# intel_oneapi_repo.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Configures the Intel oneAPI apt repository on Debian and Ubuntu."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from sushicore.errors import KeyFingerprintMismatchError
from sushicore.fragment_types import KeyPin
from sushicore.proc import CommandRunner

from .default_console import console_or_default
from .process_run import provision_runner
from .source_pins import base_key_pin
from .system import is_root

#: Where the Intel oneAPI apt repo keyring and source list are written.
K_ONEAPI_KEYRING = Path("/usr/share/keyrings/oneapi-archive-keyring.gpg")
K_ONEAPI_LIST = Path("/etc/apt/sources.list.d/oneAPI.list")
K_ONEAPI_KEY_URL = (
    "https://apt.repos.intel.com/intel-gpg-keys/GPG-PUB-KEY-INTEL-SW-PRODUCTS.PUB"
)
#: The entry of the base fragment that pins the fingerprint of the repository's signing key.
K_ONEAPI_KEY_PIN = "oneapi-apt-key"


def key_fingerprints(colon_listing: str) -> list[str]:
    """Return the primary-key fingerprints a ``gpg --show-keys --with-colons`` listing holds, in lower case.

    A subkey's fingerprint follows its own ``sub`` record and is left out; only a primary key
    can be pinned.
    """
    found: list[str] = []
    after_primary = False
    for line in colon_listing.splitlines():
        record = line.split(":")
        if record[0] == "pub":
            after_primary = True
        elif record[0] == "sub":
            after_primary = False
        elif record[0] == "fpr" and after_primary and len(record) > 9:
            found.append(record[9].lower())
            after_primary = False
    return found


def ensure_intel_oneapi_repo(dry_run: bool, runner: CommandRunner | None = None, *,
                             console: Any = None, keyring: Path = K_ONEAPI_KEYRING,
                             source_list: Path = K_ONEAPI_LIST,
                             key_pin: KeyPin | None = None) -> bool:
    """Configure the Intel oneAPI apt repository on Debian/Ubuntu, skipping a configured one.

    The key is downloaded to a file, its fingerprint is read with gpg and compared with the
    pinned one, and only the pinned key is installed into *keyring*; the source list names
    that keyring in ``signed-by``.

    Args:
        runner: Runs each step; the provision runner on *console* when ``None``.
        console: The console the steps are shown through.
        keyring: The keyring file the repository is signed with.
        source_list: The apt source list that names the repository.
        key_pin: The fingerprint the key must carry; the one the base fragment pins when ``None``.

    Returns:
        False after one error when a step fails or the downloaded file holds no key with the
        pinned fingerprint; the key is installed only after that check.
    """
    console = console_or_default(console, "ensure_intel_oneapi_repo")
    if keyring.is_file() and source_list.is_file():
        console.info("Intel oneAPI apt repository already configured.")
        return True
    pin = key_pin or base_key_pin(K_ONEAPI_KEY_PIN)
    runner = runner or provision_runner(console)
    sudo = [] if is_root() else ["sudo"]
    with tempfile.TemporaryDirectory() as scratch:
        key_file = Path(scratch) / "intel.pub"
        pinned_key = Path(scratch) / "pinned.gpg"
        listing = Path(scratch) / "oneAPI.list"
        gpg = ["gpg", "--batch", "--no-default-keyring", "--keyring", str(Path(scratch) / "ring.gpg")]
        steps = [
            ["curl", "-fsSL", "-o", str(key_file), K_ONEAPI_KEY_URL],
            [*gpg, "--import", str(key_file)],
            [*gpg, "--export", "--output", str(pinned_key), pin.fingerprint.upper()],
            [*sudo, "install", "-m", "644", str(pinned_key), str(keyring)],
            [*sudo, "install", "-m", "644", str(listing), str(source_list)],
        ]
        if dry_run:
            for step in steps:
                runner.run_drained(step, None, dry_run=True)
            return True
        listing.write_text(
            f"deb [signed-by={keyring}] https://apt.repos.intel.com/oneapi all main\n",
            encoding="utf-8")
        try:
            return _configure(runner, console, pin, key_file, steps)
        except KeyFingerprintMismatchError as error:
            console.error(str(error))
            return False


def _configure(runner: CommandRunner, console: Any, pin: KeyPin, key_file: Path,
               steps: list[list[str]]) -> bool:
    """Run *steps*, checking the fingerprint of *key_file* once the first step has fetched it.

    Raises:
        KeyFingerprintMismatchError: *key_file* holds no key with the pinned fingerprint.
    """
    failure = ("Failed to configure the Intel oneAPI apt repository "
               "(need curl and gpg). Install oneAPI manually or skip it.")
    if runner.run_drained(steps[0], None) != 0:
        console.error(failure)
        return False
    code, listing, _error = runner.capture(
        ["gpg", "--show-keys", "--with-colons", str(key_file)])
    found = key_fingerprints(listing) if code == 0 else []
    if pin.fingerprint not in found:
        raise KeyFingerprintMismatchError(key_file, pin.fingerprint, found)
    for step in steps[1:]:
        if runner.run_drained(step, None) != 0:
            console.error(failure)
            return False
    return True
