# test_monotonic_clock.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The promises every monotonic clock of the package store keeps."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import pytest

from sushicore.provision.sushi_packages.monotonic_clock import IMonotonicClock
from sushicore.provision.sushi_packages.monotonic_clock_memory import ManualMonotonicClock


@dataclass
class ClockWorld:
    """A clock under test and a way to let time pass for it."""

    clock: IMonotonicClock
    pass_time: Callable[[], None]


class ClockContract:
    """The promises every :class:`IMonotonicClock` keeps; a subclass supplies the world."""

    def test_a_read_returns_a_number_of_seconds(self, world):
        assert isinstance(world.clock(), float)

    def test_a_later_read_is_never_lower_than_an_earlier_one(self, world):
        earlier = world.clock()
        world.pass_time()
        assert world.clock() >= earlier


@pytest.mark.small
class TestManualMonotonicClockKeepsTheClockContract(ClockContract):
    """The clock that moves only when told to."""

    @pytest.fixture
    def world(self):
        clock = ManualMonotonicClock()
        return ClockWorld(clock, lambda: clock.advance(1.0))
