# quiet_console.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""A console for a runner whose caller reads results and shows no output.

It imports nothing from the package at run time, so `build_gate.py` loads it by path under
`python -I`.
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, final

if TYPE_CHECKING:
    from .proc import RichConsoleLike


@final
class QuietConsole:
    """A console for a runner whose caller reads results and shows no output; only errors reach stderr."""

    def __init__(self) -> None:
        """Bind the Rich side of this console to itself, so a printed line goes nowhere."""
        self.console: RichConsoleLike = self

    def print(self, *objects: object, **kwargs: object) -> None:
        """Drop the line."""

    def command(self, text: str) -> None:
        """Drop the echoed command."""

    def info(self, text: str) -> None:
        """Drop the message."""

    def error(self, text: str) -> None:
        """Write the message to stderr, so a command that cannot start is not silent."""
        print(text, file=sys.stderr)

    def warn(self, text: str) -> None:
        """Drop the message."""

    def is_machine(self) -> bool:
        """Return False: a quiet console renders no events."""
        return False
