# test_labels.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests which tests a set of labels selects."""

import pytest

from sushicore.testing.labels import TestLabel, select_labels

pytestmark = pytest.mark.small


@pytest.mark.parametrize("labels, every_size, include, exclude", [
    (None, False, "^(small|medium)$", "^quarantined$"),
    ([TestLabel.LARGE], False, "^(large)$", "^quarantined$"),
    ([TestLabel.SMALL], True, "^(small|medium|large)$", "^quarantined$"),
    ([TestLabel.QUARANTINED], False, "^quarantined$", None),
])
def test_labels_make_the_ctest_patterns(labels, every_size, include, exclude):
    selection = select_labels(labels, every_size=every_size)
    assert (selection.ctest_include(), selection.ctest_exclude()) == (include, exclude)


def test_a_quarantine_asked_with_a_size_keeps_the_size():
    selection = select_labels([TestLabel.SMALL, TestLabel.QUARANTINED])
    assert selection.pytest_expression() == "(small)"
    assert selection.quarantined


@pytest.mark.parametrize("labels, chosen, selected", [
    (["small"], None, True),
    (["large"], None, False),
    (["small", "quarantined"], None, False),
    (["small", "quarantined"], [TestLabel.SMALL, TestLabel.QUARANTINED], True),
    (["small"], [TestLabel.QUARANTINED], False),
    (["medium", "quarantined"], [TestLabel.QUARANTINED], True),
])
def test_a_selection_says_whether_it_runs_a_test_by_its_labels(labels, chosen, selected):
    assert select_labels(chosen).selects(labels) is selected
