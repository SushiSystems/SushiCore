# result_console.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The console a command ends on."""

from __future__ import annotations

from typing import Protocol


class ResultConsole(Protocol):
    """The one call that ends a command: its result event."""

    def result(self, ok: bool, payload: dict | None = None) -> None:
        """Report the command's outcome and its payload."""
        ...
