# test_output_memory.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the in-memory console adapter provision tests pass to what prints."""

from __future__ import annotations

import pytest

from sushicore.provision.output_memory import MemoryConsole

pytestmark = pytest.mark.small


def test_the_adapter_records_each_call_in_order_and_prints_nothing(capsys):
    """Check that calls are kept by kind and that nothing reaches the terminal."""
    console = MemoryConsole()

    console.info("one")
    console.warn("two")
    console.info("three")

    assert (console.texts("info"), console.texts("warn")) == (["one", "three"], ["two"])
    assert capsys.readouterr().out == ""
