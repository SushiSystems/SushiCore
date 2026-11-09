# test_memory_reading.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The memory reader reports a positive figure and the gate and the test run share it."""

from __future__ import annotations

import pytest

from sushicore import build_gate, memory_reading

pytestmark = pytest.mark.small


def test_free_memory_mb_reports_a_positive_figure() -> None:
    assert memory_reading.free_memory_mb() > 0


def test_build_gate_uses_the_reader_and_the_reserve_of_memory_reading() -> None:
    assert build_gate.K_RESERVE_MB == memory_reading.K_RESERVE_MB
    assert build_gate.free_memory_mb.__name__ == memory_reading.free_memory_mb.__name__
