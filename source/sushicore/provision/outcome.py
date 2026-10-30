# outcome.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""How a provisioning command ended, and the one place that reports it."""

from __future__ import annotations

from dataclasses import dataclass, field

K_EXIT_DONE = 0
K_EXIT_FAILED = 1
K_EXIT_USAGE = 2


@dataclass(frozen=True, slots=True)
class Outcome:
    """Holds how a command ended: whether it succeeded, its exit code and its result payload."""

    ok: bool
    code: int
    payload: dict = field(default_factory=dict)


def done(payload: dict | None = None) -> Outcome:
    """Returns the outcome of a command that succeeded."""
    return Outcome(True, K_EXIT_DONE, {} if payload is None else payload)


def failed(code: int = K_EXIT_FAILED, payload: dict | None = None) -> Outcome:
    """Returns the outcome of a command that failed with *code*."""
    return Outcome(False, code, {} if payload is None else payload)


def finish(console: object, outcome: Outcome) -> int:
    """Sends the one ``result`` event of a command to *console* and returns its exit code."""
    console.result(outcome.ok, outcome.payload)
    return outcome.code
