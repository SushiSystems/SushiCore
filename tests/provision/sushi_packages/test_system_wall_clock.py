# test_system_wall_clock.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The system wall clock keeps the clock contract of its interface."""

from __future__ import annotations

import pytest

from sushicore.provision.sushi_packages.system_wall_clock import SystemWallClock

from .test_wall_clock import ClockContract, ClockWorld


@pytest.mark.medium
class TestSystemWallClockKeepsTheClockContract(ClockContract):
    """The clock that reads the operating system."""

    @pytest.fixture
    def world(self):
        return ClockWorld(SystemWallClock())
