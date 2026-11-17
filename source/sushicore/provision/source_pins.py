# source_pins.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Reads the commits and key fingerprints the base fragment pins for the installers."""

from __future__ import annotations

from functools import lru_cache

from sushicore import deps_fragment
from sushicore.errors import ConfigError
from sushicore.fragment_types import Dependency, GitPin, KeyPin

from .manifests import base_fragment


@lru_cache(maxsize=1)
def _base_entries() -> dict[str, Dependency]:
    """Return the entries of the base fragment shipped in this package, by name."""
    return {dep.name: dep for dep in deps_fragment.read(base_fragment()).dependencies}


def base_git_pin(name: str) -> GitPin:
    """Return the commit the base fragment pins for the clone the entry *name* declares.

    Raises:
        ConfigError: The base fragment pins no commit under *name*.
    """
    pin = _base_entries().get(name)
    found = pin.git_pin() if pin is not None else None
    if found is None:
        raise ConfigError(
            f"The base dependency fragment pins no commit under '{name}'; "
            f"declare ref and commit under [{name}].")
    return found


def base_key_pin(name: str) -> KeyPin:
    """Return the key fingerprint the base fragment pins for the entry *name*.

    Raises:
        ConfigError: The base fragment pins no fingerprint under *name*.
    """
    pin = _base_entries().get(name)
    found = pin.key_pin() if pin is not None else None
    if found is None:
        raise ConfigError(
            f"The base dependency fragment pins no fingerprint under '{name}'; "
            f"declare fingerprint under [{name}].")
    return found
