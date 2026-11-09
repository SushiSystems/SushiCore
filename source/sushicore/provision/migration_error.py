# migration_error.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The error a migration, rollback or finalize raises when it cannot go on."""

from __future__ import annotations

from ..errors import SushiCoreError


class MigrationError(SushiCoreError):
    """Reports a migration, rollback or finalize that cannot go on."""
