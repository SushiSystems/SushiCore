# test_system_monotonic_clock.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The system monotonic clock keeps the clock contract of its interface."""

from __future__ import annotations

import pytest

from sushicore.provision.sushi_packages.system_monotonic_clock import SystemMonotonicClock

from .test_monotonic_clock import ClockContract, ClockWorld


@pytest.mark.medium
class TestSystemMonotonicClockKeepsTheClockContract(ClockContract):
    """The clock that reads the operating system."""

    @pytest.fixture
    def world(self):
        return ClockWorld(SystemMonotonicClock(), lambda: None)
