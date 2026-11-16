# wall_clock.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The wall clock port of the package store; it dates a stamp and ages a leftover."""

from __future__ import annotations

from typing import Protocol


class IWallClock(Protocol):
    """A source of the calendar time in seconds since the epoch; it may be set back."""

    def __call__(self) -> float:
        """Return the current calendar time in seconds."""
        ...
