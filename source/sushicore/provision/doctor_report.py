# doctor_report.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The outcome of a doctor run: every check paired with its result."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import final

from .check import Check
from .check_result import CheckResult
from .check_state import State


@final
@dataclass(frozen=True)
class Report:
    """The outcome of a :class:`Doctor` run: every check paired with its result."""

    rows: tuple[tuple[Check, CheckResult], ...] = field(default_factory=tuple)
    groups: frozenset[str] | None = None

    def is_required(self, check: Check) -> bool:
        """Return whether *check* counts as required: registered so, or in a requested group."""
        return check.required or (self.groups is not None and check.group in self.groups)

    def shown_state(self, check: Check, result: CheckResult) -> State:
        """Return the state this report shows for *result*: a non-required failure warns."""
        if result.state == State.FAIL and not self.is_required(check):
            return State.WARN
        return result.state

    def failures(self) -> int:
        """Return how many required checks reached :attr:`State.FAIL`."""
        return sum(
            1 for check, result in self.rows
            if self.is_required(check) and result.state == State.FAIL)

    def exit_code(self) -> int:
        """Return ``1`` when any required check failed, ``0`` otherwise."""
        return 1 if self.failures() else 0

    def payload(self) -> dict:
        """Return the payload of the report's result event: one record per check."""
        return {
            "checks": [
                {
                    "name": check.name,
                    "group": check.group,
                    "required": self.is_required(check),
                    "state": self.shown_state(check, result).value,
                    "detail": result.detail,
                    "fix": result.fix,
                }
                for check, result in self.rows
            ]
        }
