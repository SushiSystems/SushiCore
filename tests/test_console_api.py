# test_console_api.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests that the virtual terminal switch runs against an object holding only the three kernel32 calls."""

from __future__ import annotations

import pytest

from sushicore.windows_console import enable_virtual_terminal


class _ThreeCalls:
    """A kernel32 with the three calls, one console handle and one redirected handle."""

    def __init__(self) -> None:
        """Hold the console's mode."""
        self.mode = 0x0003

    def GetStdHandle(self, which: int, /) -> int | None:  # noqa: N802
        """Give the output a console handle and the error stream none."""
        return 1 if which == -11 else None

    def GetConsoleMode(self, handle, mode, /) -> int:  # noqa: N802
        """Write the mode through the pointer for the console handle only."""
        if handle != 1:
            return 0
        mode.contents.value = self.mode
        return 1

    def SetConsoleMode(self, handle, mode: int, /) -> int:  # noqa: N802
        """Take the new mode."""
        self.mode = mode
        return 1


@pytest.mark.small
def test_the_switch_sets_the_bit_on_the_console_handle_and_reports_it():
    """Check that the console handle gains the virtual terminal bit."""
    api = _ThreeCalls()
    assert enable_virtual_terminal(api, "win32") is True
    assert api.mode == 0x0003 | 0x0004
