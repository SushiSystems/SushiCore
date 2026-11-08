# test_outcome.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for how a command ends: its outcome and its one result event."""

import pytest

from sushicore.console_memory import RecordingConsole
from sushicore.provision.outcome import K_EXIT_USAGE, Outcome, done, failed, finish


@pytest.mark.small
def test_failed_passes_its_code_and_payload_through():
    """Check that failed keeps the exit code and the payload it was given."""
    assert failed(K_EXIT_USAGE, {"why": "usage"}) == Outcome(False, 2, {"why": "usage"})


@pytest.mark.small
def test_finish_sends_one_result_event_and_returns_the_exit_code():
    """Check that finish sends the outcome as one result event and returns its code."""
    console = RecordingConsole()
    assert finish(console, failed(2, {"a": 1})) == 2
    assert [(name, args) for name, args in console.calls] == [("result", (False, {"a": 1}))]


@pytest.mark.small
def test_two_outcomes_do_not_share_a_payload():
    """Check that changing one outcome's payload leaves another's empty."""
    first, second = done(), done()
    first.payload["x"] = 1
    assert second.payload == {}
