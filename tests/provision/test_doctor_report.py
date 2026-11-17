# test_doctor_report.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the report a doctor run produces."""

from __future__ import annotations

import pytest

from sushicore.provision.check_result import CheckResult
from sushicore.provision.check_state import State
from sushicore.provision.doctor_report import Report
from sushicore.provision.function_check import FunctionCheck


def _row(name, group, required, state):
    """Return one report row for a check of *name* that reached *state*."""
    return (FunctionCheck(name, group, required, lambda: CheckResult(state, name)),
            CheckResult(state, name, "fix"))


@pytest.mark.small
def test_an_optional_failure_shows_as_a_warning_until_its_group_is_asked_for():
    """Check that shown_state demotes an optional failure unless its group was requested."""
    check, result = _row("torch", "infer", False, State.FAIL)
    assert Report(((check, result),)).shown_state(check, result) is State.WARN
    assert Report(((check, result),), frozenset({"infer"})).shown_state(check, result) is State.FAIL


@pytest.mark.small
def test_the_payload_lists_one_record_per_check():
    """Check that the payload carries the name, group, requirement, shown state, detail and fix."""
    row = _row("cmake", "build", True, State.OK)
    assert Report((row,)).payload() == {"checks": [{
        "name": "cmake", "group": "build", "required": True, "state": "ok",
        "detail": "cmake", "fix": "fix"}]}
