# test_console_output.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for what the detect step prints through its console."""

from __future__ import annotations

import pytest

from sushicore.console_memory import RecordingConsole
from sushicore.provision.config import ProvisionSettings
from sushicore.provision.fragments_memory import InMemoryDependencySource
from sushicore.provision.pipeline import InstallContext
from sushicore.provision.detect_step import DetectStep


pytestmark = pytest.mark.small


@pytest.mark.parametrize(("machine", "expected"), [
    (False, "ninja  \\[bold]odd"),
    (True, "ninja  [bold]odd"),
])
def test_a_missing_detail_is_escaped_for_a_terminal_and_left_alone_in_machine_mode(
        machine, expected):
    """Check that the missing-component line escapes Rich markup only when a terminal reads it."""
    recording = RecordingConsole(machine=machine)
    rows = [("ninja", "MISSING", "shared", "[bold]odd")]
    ctx = InstallContext(cfg=ProvisionSettings(platform="linux"))
    DetectStep(InMemoryDependencySource([]), console=recording).report_inventory(ctx, rows)
    assert expected in recording.texts("info")
