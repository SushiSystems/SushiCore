# test_check_result.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the outcome of one check's run."""

from __future__ import annotations

import pytest

from sushicore.provision.check_result import CheckResult
from sushicore.provision.check_state import State


@pytest.mark.small
def test_a_result_without_a_fix_carries_an_empty_one():
    """Check that the fix defaults to an empty string."""
    assert CheckResult(State.OK, "found").fix == ""
