# quiet_runner.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The real command runner for a caller that reads results and shows no output."""

from __future__ import annotations

from .proc import Runner
from .quiet_console import QuietConsole


def quiet_runner() -> Runner:
    """Return the real runner for a caller that reads results and shows no output."""
    return Runner(QuietConsole(), "sushicore")
