# message_console.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The console a unit prints its messages through."""

from __future__ import annotations

from typing import Protocol


class MessageConsole(Protocol):
    """The four message calls of a CLI's console, which a unit that only reports needs."""

    def info(self, msg: str, /) -> None:
        """Print an informational message."""
        ...

    def success(self, msg: str, /) -> None:
        """Print a success message."""
        ...

    def warn(self, msg: str, /) -> None:
        """Print a warning."""
        ...

    def error(self, msg: str, /) -> None:
        """Print an error."""
        ...
