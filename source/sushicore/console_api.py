# console_api.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The Windows console calls that switch on virtual terminal processing."""

from __future__ import annotations

from typing import Protocol


class ConsoleApi(Protocol):
    """The three kernel32 calls :func:`sushicore.windows_console.enable_virtual_terminal` makes."""

    def GetStdHandle(self, which: int, /) -> int | None:  # noqa: N802
        """Return the handle of a standard stream, or None when it has none."""
        ...

    def GetConsoleMode(self, handle: int | None, mode: object, /) -> int:  # noqa: N802
        """Write the mode of a console handle through *mode*; return non-zero on success."""
        ...

    def SetConsoleMode(self, handle: int | None, mode: int, /) -> int:  # noqa: N802
        """Set the mode of a console handle; return non-zero on success."""
        ...
