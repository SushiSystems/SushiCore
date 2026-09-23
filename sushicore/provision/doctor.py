# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""The doctor framework: checks, their results and a runner that reports them."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Callable, Collection, Protocol, Sequence

GROUPS = ("build", "test", "infer", "eval")


class State(enum.Enum):
    """The outcome a single check reaches."""

    OK = "ok"
    WARN = "warn"
    FAIL = "fail"
    SKIP = "skip"


@dataclass(frozen=True)
class CheckResult:
    """The outcome of one check's run, with the detail a report line shows.

    Args:
        fix: The command that resolves a non-OK state, empty when there is none.
    """

    state: State
    detail: str
    fix: str = ""


class Check(Protocol):
    """A single named, grouped diagnostic that a :class:`Doctor` can run."""

    name: str
    group: str
    required: bool

    def run(self) -> CheckResult:
        """Run the diagnostic and return its outcome."""
        ...


@dataclass
class FunctionCheck:
    """Adapts a zero-argument callable returning :class:`CheckResult` into a :class:`Check`."""

    name: str
    group: str
    required: bool
    fn: Callable[[], CheckResult]

    def run(self) -> CheckResult:
        """Call the wrapped function and return its result."""
        return self.fn()


@dataclass(frozen=True)
class Report:
    """The outcome of a :class:`Doctor` run: every check paired with its result."""

    rows: tuple[tuple[Check, CheckResult], ...] = field(default_factory=tuple)

    def failures(self) -> int:
        """Return how many required checks reached :attr:`State.FAIL`."""
        return sum(
            1 for check, result in self.rows if check.required and result.state == State.FAIL)

    def exit_code(self) -> int:
        """Return ``1`` when any required check failed, ``0`` otherwise."""
        return 1 if self.failures() else 0


_STATE_MARKUP = {
    State.OK: "[success]ok[/success]",
    State.WARN: "[warn]warn[/warn]",
    State.FAIL: "[error]FAIL[/error]",
    State.SKIP: "[dim]skip[/dim]",
}


def _markup(check: Check, result: CheckResult) -> str:
    """Return the table markup for *result*, downgrading a non-required failure to a warning."""
    if result.state == State.FAIL and not check.required:
        return "[warn]warn[/warn]"
    return _STATE_MARKUP[result.state]


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
        return Report(tuple(rows))

    def render(self, report: Report, console: object) -> None:
        """Print *report* as a table followed by a result, through *console*."""
        rows = [
            [check.name, check.group, _markup(check, result), result.detail, result.fix]
            for check, result in report.rows
        ]
        console.table(["Check", "Group", "Result", "Detail", "Fix"], rows, title="Doctor")
        payload = {
            "checks": [
                {
                    "name": check.name,
                    "group": check.group,
                    "required": check.required,
                    "state": result.state.value,
                    "detail": result.detail,
                    "fix": result.fix,
                }
                for check, result in report.rows
            ]
        }
        console.result(report.exit_code() == 0, payload)
