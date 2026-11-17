# step_result.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The outcome one pipeline step reports."""

from __future__ import annotations

import enum


class StepResult(enum.Enum):
    """Outcome of a single pipeline step."""

    OK = "ok"
    SKIPPED = "skipped"
    FAILED = "failed"
