# test_adapter_builder_memory.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""What the in-memory command runner and adapter builder promise as stand-ins for their ports."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from sushicore.provision.gpu.adapter_builder_memory import (
    InMemoryAdapterBuilder,
    InMemoryCommandRunner,
)

pytestmark = pytest.mark.small


def test_a_runner_records_each_command_in_order_and_succeeds():
    """Check that every command is recorded in order and exits 0."""
    runner = InMemoryCommandRunner()

    codes = [runner.run(["git", "init"], None, None), runner.run(["cmake", "--build"], None, None)]

    assert codes == [0, 0]
    assert runner.calls == [["git", "init"], ["cmake", "--build"]]


def test_a_runner_fails_only_the_command_holding_the_word_it_was_told():
    """Check that only a command whose argv holds the word exits 1."""
    runner = InMemoryCommandRunner(fail_on="-S")

    assert runner.run(["git", "init"], None, None) == 0
    assert runner.run(["cmake", "-S", "src"], None, None) == 1


def test_a_runner_told_the_executable_is_missing_raises_after_recording():
    """Check that a missing executable raises FileNotFoundError and the call is still recorded."""
    runner = InMemoryCommandRunner(missing=True)

    with pytest.raises(FileNotFoundError):
        runner.run(["git", "init"], None, None)

    assert runner.calls == [["git", "init"]]


def test_a_builder_records_the_vendor_of_each_build_in_order():
    """Check that each build adds its vendor to the record."""
    builder = InMemoryAdapterBuilder()

    builder.build(SimpleNamespace(vendor="cuda"), None, Path("t"), "abc", dry_run=False)
    builder.build(SimpleNamespace(vendor="rocm"), None, Path("t"), "abc", dry_run=False)

    assert builder.built == ["cuda", "rocm"]


@pytest.mark.parametrize(("vendor", "expected"), [("cuda", True), ("rocm", False), ("other", True)],
                         ids=["succeeds", "fails", "unlisted-succeeds"])
def test_a_builder_answers_the_outcome_of_the_vendor(vendor, expected):
    """Check that the outcome follows the vendor, and a vendor left out succeeds."""
    builder = InMemoryAdapterBuilder({"cuda": True, "rocm": False})

    result = builder.build(SimpleNamespace(vendor=vendor), None, Path("t"), "abc", dry_run=False)

    assert result is expected
