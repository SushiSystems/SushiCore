# test_quiet_console.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the console of a runner that shows no output."""

import sys

import pytest

from sushicore.quiet_console import QuietConsole


@pytest.mark.small
def test_a_quiet_console_writes_only_errors_to_stderr(capfd):
    console = QuietConsole()
    console.command("tool")
    console.info("note")
    console.warn("careful")
    console.error("broken")
    console.console.print("line")
    captured = capfd.readouterr()
    assert (captured.out, captured.err.strip(), console.is_machine()) == ("", "broken", False)
