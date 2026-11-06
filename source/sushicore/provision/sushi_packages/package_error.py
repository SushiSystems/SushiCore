# package_error.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The failures the Sushi package resolver raises."""

from __future__ import annotations

from ...errors import SushiCoreError


class PackageError(SushiCoreError):
    """Raised when a Sushi package cannot be keyed, built, found or chosen."""


class PackageConflictError(PackageError):
    """Raised when one library would appear in a closure at two different keys."""
