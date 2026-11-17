# test_check_state.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the outcome a doctor check reaches."""

from __future__ import annotations

import pytest

from sushicore.provision.check_state import State


@pytest.mark.small
def test_the_states_carry_their_reported_names():
    """Check that the four outcomes keep the values a payload carries."""
    assert [state.value for state in State] == ["ok", "warn", "fail", "skip"]
