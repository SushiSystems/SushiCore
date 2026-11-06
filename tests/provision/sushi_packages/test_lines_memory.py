# test_lines_memory.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the line sink that keeps what it receives."""

from __future__ import annotations

import pytest

from sushicore.provision.sushi_packages.lines_memory import RecordedLines

pytestmark = pytest.mark.small


def test_a_sink_keeps_its_lines_in_the_order_they_came():
    """Check that two lines are kept, first line first."""
    sink = RecordedLines()
    sink("first")
    sink("second")
    assert sink.lines == ["first", "second"]

