# report_console.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The console a diagnostic report prints through."""

from __future__ import annotations

from typing import Protocol


class ReportConsole(Protocol):
    """The calls a report makes: a header, lines of text, an error and a table."""

    def header(self, title: str, /) -> None:
        """Print a section title."""
        ...

    def info(self, msg: str, /) -> None:
        """Print an informational message."""
        ...

    def error(self, msg: str, /) -> None:
        """Print an error."""
        ...

    def table(self, columns: list[str], rows: list[list[str]], title: str = "") -> None:
        """Print a table of string cells."""
        ...
