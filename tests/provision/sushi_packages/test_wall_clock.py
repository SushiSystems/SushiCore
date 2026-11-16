# test_wall_clock.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The one promise every wall clock keeps; a wall clock may be set back, so it promises no order."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from sushicore.provision.sushi_packages.wall_clock import IWallClock
from sushicore.provision.sushi_packages.wall_clock_memory import ManualWallClock


@dataclass
class ClockWorld:
    """A wall clock under test."""

    clock: IWallClock


class ClockContract:
    """The promises every :class:`IWallClock` keeps; a subclass supplies the world."""

    def test_a_read_returns_a_number_of_seconds(self, world):
        assert isinstance(world.clock(), float)


@pytest.mark.small
class TestManualWallClockKeepsTheClockContract(ClockContract):
    """The clock that moves only when told to."""

    @pytest.fixture
    def world(self):
        return ClockWorld(ManualWallClock())
