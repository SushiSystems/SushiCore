# test_cuda_selection_memory.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""What the table architecture probe promises as a stand-in for the compiler query."""

from __future__ import annotations

import pytest

from sushicore.provision.gpu.cuda_selection_memory import TableArchitectureProbe

pytestmark = pytest.mark.small


def test_the_probe_answers_the_row_of_the_versions_major():
    """Check that each version gets the architectures of its major."""
    probe = TableArchitectureProbe({12: frozenset({"61"}), 13: frozenset({"75"})})

    assert probe((13, 1, 2)) == frozenset({"75"})
    assert probe((12, 6, 3)) == frozenset({"61"})


def test_the_probe_does_not_follow_later_changes_to_the_table_it_was_given():
    """Check that the probe copies its table."""
    table = {13: frozenset({"75"})}
    probe = TableArchitectureProbe(table)
    table[13] = frozenset({"89"})

    assert probe((13, 0, 0)) == frozenset({"75"})


def test_the_probe_raises_for_a_major_the_table_lacks():
    """Check that an unknown major is a KeyError, not an empty answer."""
    with pytest.raises(KeyError):
        TableArchitectureProbe({13: frozenset({"75"})})((11, 0, 0))
