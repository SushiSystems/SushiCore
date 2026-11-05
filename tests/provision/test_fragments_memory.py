# test_fragments_memory.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""What the in-memory dependency source promises beyond its contract."""

from __future__ import annotations

import pytest

from sushicore.provision.fragments import Dependency
from sushicore.provision.fragments_memory import InMemoryDependencySource

pytestmark = pytest.mark.small


def test_the_source_does_not_follow_later_changes_to_the_list_it_was_given():
    declared = [Dependency(name="cmake")]
    source = InMemoryDependencySource(declared)
    declared.append(Dependency(name="ninja"))
    assert [dep.name for dep in source.all()] == ["cmake"]


def test_a_list_returned_by_all_can_be_changed_without_changing_the_source():
    source = InMemoryDependencySource([Dependency(name="cmake")])
    source.all().clear()
    assert [dep.name for dep in source.all()] == ["cmake"]


def test_a_list_returned_by_depends_on_can_be_changed_without_changing_the_source():
    source = InMemoryDependencySource([], {"m": ["sushilog"]})
    source.depends_on("m").clear()
    assert source.depends_on("m") == ["sushilog"]
