# test_step_result.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the outcome a pipeline step reports."""

from __future__ import annotations

import pytest

from sushicore.provision.step_result import StepResult


@pytest.mark.small
def test_the_outcomes_carry_their_reported_names():
    """Check that the three outcomes keep the values a log line prints."""
    assert [result.value for result in StepResult] == ["ok", "skipped", "failed"]
