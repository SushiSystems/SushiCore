# check_result.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The outcome of one check's run, with the detail a report line shows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import final

from .check_state import State


@final
@dataclass(frozen=True)
class CheckResult:
    """The outcome of one check's run, with the detail a report line shows.

    Args:
        fix: The command that resolves a non-OK state, empty when there is none.
    """

    state: State
    detail: str
    fix: str = ""
