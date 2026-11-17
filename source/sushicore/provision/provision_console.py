# provision_console.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The console the provision commands and install steps print through."""

from __future__ import annotations

from typing import Protocol

from ..proc import ConsoleLike


class ProvisionConsole(ConsoleLike, Protocol):
    """A CLI's console as the install run uses it: messages, commands, headers, progress and results."""

    def success(self, text: str) -> None:
        """Print a success message."""
        ...

    def header(self, title: str) -> None:
        """Print a section title."""
        ...

    def progress(self, label: str, index: int, count: int, fraction: float | None = None) -> None:
        """Report step *index* of *count* for *label*."""
        ...

    def table(self, columns: list[str], rows: list[list[str]], title: str = "") -> None:
        """Print a table of string cells."""
        ...

    def result(self, ok: bool, payload: dict | None = None) -> None:
        """Report the command's outcome and its payload."""
        ...
