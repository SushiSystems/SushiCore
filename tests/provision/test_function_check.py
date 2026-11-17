# test_function_check.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the check that wraps a function."""

from __future__ import annotations

import pytest

from sushicore.provision.check_result import CheckResult
from sushicore.provision.check_state import State
from sushicore.provision.function_check import FunctionCheck


@pytest.mark.small
def test_run_returns_what_the_wrapped_function_returns():
    """Check that the wrapped function's result comes back unchanged."""
    result = CheckResult(State.WARN, "old", "upgrade")
    check = FunctionCheck("cmake", "build", False, lambda: result)
    assert check.run() is result
