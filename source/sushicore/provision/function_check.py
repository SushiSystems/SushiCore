# function_check.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""A check that wraps a zero-argument function."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, final

from .check_result import CheckResult


@final
@dataclass(frozen=True, slots=True)
class FunctionCheck:
    """Adapts a zero-argument callable returning :class:`CheckResult` into a :class:`Check`."""

    name: str
    group: str
    required: bool
    fn: Callable[[], CheckResult]

    def run(self) -> CheckResult:
        """Call the wrapped function and return its result."""
        return self.fn()
