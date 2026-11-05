# test_clock_memory.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""What the manual clock promises beyond the clock contract in test_clock.py."""

from __future__ import annotations

import pytest

from sushicore.provision.sushi_packages.clock_memory import ManualClock

pytestmark = pytest.mark.small


def test_a_manual_clock_reads_the_same_time_until_it_is_advanced():
    clock = ManualClock(5.0)
    assert (clock(), clock()) == (5.0, 5.0)


def test_advancing_a_manual_clock_moves_it_by_the_seconds_given():
    clock = ManualClock(5.0)
    clock.advance(2.5)
    assert clock() == 7.5
