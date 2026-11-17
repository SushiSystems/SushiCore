# check_state.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The outcome a single doctor check reaches."""

from __future__ import annotations

import enum


class State(enum.Enum):
    """The outcome a single check reaches."""

    OK = "ok"
    WARN = "warn"
    FAIL = "fail"
    SKIP = "skip"
