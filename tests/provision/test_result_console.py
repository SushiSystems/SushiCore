# test_result_console.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests that a command ends on a console holding only the result call."""

from __future__ import annotations

import pytest

from sushicore.provision.outcome import done, finish


class _ResultOnly:
    """A console that keeps the result events it is sent."""

    def __init__(self) -> None:
        """Start with no event."""
        self.events: list[tuple[bool, dict | None]] = []

    def result(self, ok: bool, payload: dict | None = None) -> None:
        """Record the event."""
        self.events.append((ok, payload))


@pytest.mark.small
def test_finish_sends_one_result_and_returns_the_exit_code():
    """Check that a done outcome sends one ok event and exits zero."""
    console = _ResultOnly()
    assert finish(console, done({"checked": 1})) == 0
    assert console.events == [(True, {"checked": 1})]
