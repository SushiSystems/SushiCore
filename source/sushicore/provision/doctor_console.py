# doctor_console.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The console a doctor report prints through."""

from __future__ import annotations

from typing import Protocol

from .result_console import ResultConsole


class DoctorConsole(ResultConsole, Protocol):
    """The calls a doctor report makes: its table, then its result event."""

    def table(self, columns: list[str], rows: list[list[str]], title: str = "") -> None:
        """Print a table of string cells."""
        ...
