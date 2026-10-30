# test_outcome.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests how a provisioning command's ending is built and reported."""

import pytest

from sushicore.provision.outcome import K_EXIT_USAGE, Outcome, done, failed, finish


pytestmark = pytest.mark.small


class _Console:
    def __init__(self):
        self.results = []

    def result(self, ok, payload):
        self.results.append((ok, payload))


def test_done_succeeds_with_exit_code_zero_and_an_empty_payload():
    assert done() == Outcome(True, 0, {})


def test_failed_defaults_to_exit_code_one_and_accepts_a_code_and_a_payload():
    assert failed() == Outcome(False, 1, {})
    assert failed(K_EXIT_USAGE, {"why": "usage"}) == Outcome(False, 2, {"why": "usage"})


def test_finish_sends_one_result_event_and_returns_the_exit_code():
    console = _Console()
    assert finish(console, failed(2, {"a": 1})) == 2
    assert console.results == [(False, {"a": 1})]


def test_two_outcomes_do_not_share_a_payload():
    first, second = done(), done()
    first.payload["x"] = 1
    assert second.payload == {}
