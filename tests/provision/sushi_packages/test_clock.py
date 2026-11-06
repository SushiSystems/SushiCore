# test_clock.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The promises every clock of the package store keeps."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass

import pytest

from sushicore.provision.sushi_packages.clock import Clock
from sushicore.provision.sushi_packages.clock_memory import ManualClock


@dataclass
class ClockWorld:
    """A clock under test and a way to let time pass for it."""

    clock: Clock
    pass_time: Callable[[], None]


class ClockContract:
    """The promises every :class:`Clock` keeps; a subclass supplies the world."""

    def test_a_read_returns_a_number_of_seconds(self, world):
        assert isinstance(world.clock(), float)

    def test_a_later_read_is_never_lower_than_an_earlier_one(self, world):
        earlier = world.clock()
        world.pass_time()
        assert world.clock() >= earlier


@pytest.mark.small
class TestManualClockKeepsTheClockContract(ClockContract):
    """The clock that moves only when told to."""

    @pytest.fixture
    def world(self):
        clock = ManualClock()
        return ClockWorld(clock, lambda: clock.advance(1.0))


@pytest.mark.medium
class TestSystemClocksKeepTheClockContract(ClockContract):
    """The clocks the store and the resolver default to."""

    @pytest.fixture(params=[time.time, time.monotonic], ids=["time", "monotonic"])
    def world(self, request):
        return ClockWorld(request.param, lambda: None)
