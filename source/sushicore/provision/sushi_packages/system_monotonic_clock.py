# system_monotonic_clock.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The monotonic clock adapter that reads the operating system."""

from __future__ import annotations

import time
from typing import final


@final
class SystemMonotonicClock:
    """Reads the monotonic time from the operating system."""

    def __call__(self) -> float:
        """Return :func:`time.monotonic`."""
        return time.monotonic()
