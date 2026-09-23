# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for the console seam moved code prints through."""

from __future__ import annotations

import pytest

import sushicore
from sushicore import provision
from sushicore.provision import steps
from sushicore.provision._output import console


def test_calls_reach_the_bound_console(recording_console):
    """Check that console calls reach the bound console."""
    console.info("hello")
    assert recording_console.calls == [("info", ("hello",))]


def test_unbound_console_raises_a_named_error():
    """Check that an unbound console raises a named error."""
    provision.bind_console(None)
    with pytest.raises(RuntimeError, match="bind_console"):
        console.info("x")


def test_provider_is_called_lazily():
    """Check that the console provider is called lazily."""
    calls = []

    class Fake:
        def info(self, msg):
            calls.append(msg)

    provision.bind_console(lambda: Fake())
    assert calls == []
    console.info("late")
    assert calls == ["late"]
    provision.bind_console(None)


def test_a_plain_console_answers_is_machine_for_steps_literal():
    """Check that steps._literal survives a real Console's is_machine() call."""
    provision.bind_console(lambda: sushicore.build_console([]))
    try:
        assert steps._literal("hello") == "hello"
    finally:
        provision.bind_console(None)
