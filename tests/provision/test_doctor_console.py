# test_doctor_console.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests that a doctor report prints through a console holding only the table and the result."""

from __future__ import annotations

import pytest

from sushicore.provision.check_result import CheckResult
from sushicore.provision.check_state import State
from sushicore.provision.doctor import Doctor
from sushicore.provision.function_check import FunctionCheck


class _TableAndResult:
    """A console holding the two calls a doctor report makes."""

    def __init__(self) -> None:
        """Start with nothing printed."""
        self.calls: list[str] = []

    def table(self, columns: list[str], rows: list[list[str]], title: str = "") -> None:
        """Record the table."""
        self.calls.append("table")

    def result(self, ok: bool, payload: dict | None = None) -> None:
        """Record the result event."""
        self.calls.append("result")


@pytest.mark.small
def test_render_prints_the_table_then_the_result():
    """Check that rendering a report makes exactly those two calls, in that order."""
    console = _TableAndResult()
    doctor = Doctor([FunctionCheck("cmake", "build", True, lambda: CheckResult(State.OK, "found"))])
    doctor.render(doctor.run(), console)
    assert console.calls == ["table", "result"]
