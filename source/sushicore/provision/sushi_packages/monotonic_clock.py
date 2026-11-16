# monotonic_clock.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The monotonic clock port of the package resolver; it measures how long a build took."""

from __future__ import annotations

from typing import Protocol


class IMonotonicClock(Protocol):
    """A source of seconds from an arbitrary start that never reads lower than an earlier read."""

    def __call__(self) -> float:
        """Return the current monotonic time in seconds."""
        ...
