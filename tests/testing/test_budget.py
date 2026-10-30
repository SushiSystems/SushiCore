# test_budget.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests what a run is judged as and the call of the budget reader."""

import pytest

from sushicore.testing.budget import large_needs_a_filter, reader_command, scope_of
from sushicore.testing.labels import TestLabel, select_labels

pytestmark = pytest.mark.small


@pytest.mark.parametrize("labels, filtered, every_size, repeated, scope", [
    (None, False, False, False, "default"),
    (None, True, False, False, "partial"),
    (None, False, False, True, "partial"),
    ([TestLabel.SMALL], False, False, False, "partial"),
    (None, False, True, False, "large"),
    ([TestLabel.LARGE], True, False, False, "partial"),
])
def test_a_run_is_default_only_when_nothing_narrowed_it(labels, filtered, every_size, repeated, scope):
    selection = select_labels(labels, every_size=every_size)
    assert scope_of(selection, filtered=filtered, every_size=every_size, repeated=repeated) == scope


@pytest.mark.parametrize("labels, filtered, every_size, refused", [
    ([TestLabel.LARGE], False, False, True),
    ([TestLabel.LARGE], True, False, False),
    (None, False, True, False),
    (None, False, False, False),
])
def test_the_large_tests_start_only_when_something_narrows_them(labels, filtered, every_size, refused):
    selection = select_labels(labels, every_size=every_size)
    assert large_needs_a_filter(selection, filtered=filtered, every_size=every_size) is refused


def test_the_reader_is_called_only_where_the_repository_carries_it(tmp_path):
    junit = tmp_path / "junit.xml"
    assert reader_command(tmp_path, junit, "default", 3.0) is None
    (tmp_path / "tools" / "testing").mkdir(parents=True)
    (tmp_path / "tools" / "testing" / "test_budget.py").write_text("", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "budget_exemptions.toml").write_text("", encoding="utf-8")
    command = reader_command(tmp_path, junit, "default", 3.04)
    assert command[2:4] == [str(junit), "--scope"] and command[4:6] == ["default", "--wall"]
    assert command[6] == "3.0"
    assert command[-2] == "--exemptions"
