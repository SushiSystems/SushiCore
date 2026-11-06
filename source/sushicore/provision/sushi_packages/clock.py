# clock.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The clock port of the package store and resolver; ``time.time`` and ``time.monotonic`` fit it."""

from __future__ import annotations

from typing import Protocol


class Clock(Protocol):
    """A source of the time in seconds that never reads lower than an earlier read."""

    def __call__(self) -> float:
        """Return the current time in seconds."""
        ...
