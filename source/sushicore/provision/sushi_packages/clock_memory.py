# clock_memory.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""A clock that moves only when told to, for tests of code that reads the time."""

from __future__ import annotations


class ManualClock:
    """Reads a fixed time until :meth:`advance` moves it; the real clock is never read.

    Args:
        now: The time in seconds the clock starts at.
    """

    def __init__(self, now: float = 1000.0) -> None:
        """Start at *now* seconds."""
        self.now = now

    def __call__(self) -> float:
        """Return the current time in seconds."""
        return self.now

    def advance(self, seconds: float) -> None:
        """Move the clock forward by *seconds*."""
        self.now += seconds
