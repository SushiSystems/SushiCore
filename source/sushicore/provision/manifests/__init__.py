# __init__.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The dependency fragment every SYCL module shares."""

from __future__ import annotations

from pathlib import Path

#: Owner label carried by the dependencies the base fragment declares.
BASE_OWNER = "shared"


def base_fragment() -> Path:
    """Return the path of the base fragment shipped in this package."""
    return Path(__file__).with_name("base.deps.toml")
