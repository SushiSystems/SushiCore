# lines_memory.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""A line sink that keeps what it receives, for a warning or a report that prints nothing."""

from __future__ import annotations


class RecordedLines:
    """Keeps every line it is given, in order.

    Attributes:
        lines: The lines received so far.
    """

    def __init__(self) -> None:
        """Start with no line."""
        self.lines: list[str] = []

    def __call__(self, line: str) -> None:
        """Keep *line*."""
        self.lines.append(line)
