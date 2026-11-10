# test_environment_memory.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""What both environment adapters promise: the contract of the Environment port."""

from __future__ import annotations

import pytest

from sushicore.environment_memory import MemoryEnvironment

pytestmark = pytest.mark.small


def test_a_held_variable_is_read_and_an_absent_one_takes_the_default():
    environment = MemoryEnvironment({"A": "1"})
    assert environment.get("A") == "1"
    assert environment.get("B") is None
    assert environment.get("B", "fallback") == "fallback"


def test_an_empty_value_still_counts_as_set():
    environment = MemoryEnvironment({"A": ""})
    assert environment.has("A") and not environment.has("B")


def test_the_memory_environment_never_reads_the_process(monkeypatch):
    monkeypatch.setenv("SUSHICORE_TEST_ONLY", "x")
    assert not MemoryEnvironment().has("SUSHICORE_TEST_ONLY")
