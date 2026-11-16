# test_console_output.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the console seam moved code prints through."""

from __future__ import annotations

import pytest

from sushicore.console_memory import RecordingConsole
from sushicore.provision._output import ConsoleProxy
from sushicore.provision.config import ProvisionSettings
from sushicore.provision.fragments_memory import InMemoryDependencySource
from sushicore.provision.pipeline import InstallContext
from sushicore.provision.steps import DetectStep


pytestmark = pytest.mark.small


def test_calls_reach_the_bound_console():
    """Check that a call on the proxy reaches the console its provider returns."""
    recording = RecordingConsole()
    proxy = ConsoleProxy()
    proxy.bind(lambda: recording)
    proxy.info("hello")
    assert recording.texts("info") == ["hello"]


def test_unbound_console_raises_a_named_error():
    """Check that a proxy with no provider names bind_console in its error."""
    with pytest.raises(RuntimeError, match="bind_console"):
        ConsoleProxy().info("x")


def test_unbinding_a_console_raises_the_named_error_again():
    """Check that binding None takes the console away."""
    proxy = ConsoleProxy()
    proxy.bind(lambda: RecordingConsole())
    proxy.bind(None)
    with pytest.raises(RuntimeError, match="bind_console"):
        proxy.info("x")


def test_provider_is_not_called_until_the_console_is_used():
    """Check that binding a provider does not call it."""
    asked = []
    proxy = ConsoleProxy()
    proxy.bind(lambda: asked.append("asked"))
    assert asked == []


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
