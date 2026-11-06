# errors.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The failures the design commands report as one line."""

from __future__ import annotations

from ..errors import SushiCoreError


class DesignError(SushiCoreError):
    """Reports a design tree that cannot be read or a change the design commands refuse."""


class TopicNotFoundError(DesignError):
    """Reports a name that is not a design topic."""


class OwnedModuleError(DesignError):
    """Reports a module another topic already owns."""
