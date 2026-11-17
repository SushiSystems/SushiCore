# check.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The contract one named, grouped diagnostic implements."""

from __future__ import annotations

from typing import Protocol

from .check_result import CheckResult


class Check(Protocol):
    """A single named, grouped diagnostic that a :class:`Doctor` can run."""

    name: str
    group: str
    required: bool

    def run(self) -> CheckResult:
        """Run the diagnostic and return its outcome."""
        ...
