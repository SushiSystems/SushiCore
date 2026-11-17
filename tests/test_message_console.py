# test_message_console.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests that a unit needing only the four message calls runs against a console with only those."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.cmake_driver import CMakeDriver
from sushicore.console_memory import RecordingConsole
from sushicore.proc_memory import RecordingRunner


class _FourCalls:
    """A console holding the four message calls and nothing else."""

    def __init__(self) -> None:
        """Start with no message."""
        self.messages: list[tuple[str, str]] = []

    def info(self, msg: str, /) -> None:
        """Record an informational message."""
        self.messages.append(("info", msg))

    def success(self, msg: str, /) -> None:
        """Record a success message."""
        self.messages.append(("success", msg))

    def warn(self, msg: str, /) -> None:
        """Record a warning."""
        self.messages.append(("warn", msg))

    def error(self, msg: str, /) -> None:
        """Record an error."""
        self.messages.append(("error", msg))


@pytest.mark.medium
def test_the_cmake_driver_reports_a_clean_through_the_four_message_calls(tmp_path):
    """Check that cleaning an existing tree says what it removes and that it was removed."""
    console = _FourCalls()
    tree = tmp_path / "build"
    tree.mkdir()
    CMakeDriver(console, RecordingRunner(RecordingConsole())).clean_tree(tree)
    assert console.messages == [("info", f"Removing {tree}..."), ("success", f"{tree} removed.")]
