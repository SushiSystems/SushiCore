# doctor.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Runs a set of doctor checks and prints their report.

``Check``, ``CheckResult``, ``FunctionCheck``, ``Report`` and ``State`` are re-exported for the
module CLIs that import them from here.
"""

from __future__ import annotations

from typing import Collection, Sequence

from .check import Check
from .check_result import CheckResult
from .check_state import State
from .doctor_console import DoctorConsole
from .doctor_report import Report
from .function_check import FunctionCheck  # noqa: F401

GROUPS = ("build", "test", "infer", "eval")


_STATE_MARKUP = {
    State.OK: "[success]ok[/success]",
    State.WARN: "[warn]warn[/warn]",
    State.FAIL: "[error]FAIL[/error]",
    State.SKIP: "[dim]skip[/dim]",
}


def _markup(report: Report, check: Check, result: CheckResult) -> str:
    """Return the table markup for the state *report* shows for *result*."""
    return _STATE_MARKUP[report.shown_state(check, result)]


class Doctor:
    """Runs a set of checks, filtered by group, and reports their outcome."""

    def __init__(self, checks: Sequence[Check]) -> None:
        """Bind the checks this doctor runs."""
        self._checks = list(checks)

    def run(self, groups: Collection[str] | None = None) -> Report:
        """Run every check whose group is in *groups*, or all checks when *groups* is None.

        Args:
            groups: Group names to restrict the run to, or None to run every check.
        """
        rows: list[tuple[Check, CheckResult]] = []
        for check in self._checks:
            if groups is not None and check.group not in groups:
                continue
            try:
                result = check.run()
            except Exception as exc:  # noqa: BLE001
                result = CheckResult(State.FAIL, f"{type(exc).__name__}: {exc}")
            rows.append((check, result))
        return Report(tuple(rows), None if groups is None else frozenset(groups))

    def render_table(self, report: Report, console: DoctorConsole) -> None:
        """Print *report* as a table through *console*, without the closing result event."""
        rows = [
            [check.name, check.group, _markup(report, check, result), result.detail, result.fix]
            for check, result in report.rows
        ]
        console.table(["Check", "Group", "Result", "Detail", "Fix"], rows, title="Doctor")

    def render(self, report: Report, console: DoctorConsole) -> None:
        """Print *report* as a table followed by its result event, through *console*."""
        self.render_table(report, console)
        console.result(report.exit_code() == 0, report.payload())
