# test_package_lists.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""What dedup returns for a list of package names."""

from __future__ import annotations

import pytest

from sushicore.provision.package_lists import dedup


pytestmark = pytest.mark.small


@pytest.mark.parametrize(("names", "expected"), [
    (["git", "cmake", "git", "ninja", "cmake"], ["git", "cmake", "ninja"]),
    (["git", "cmake"], ["git", "cmake"]),
    ([], []),
])
def test_dedup_keeps_each_name_once_in_first_seen_order(names, expected):
    """Check that dedup drops repeats and keeps the order the names were first met in."""
    assert dedup(names) == expected


def test_dedup_leaves_the_list_it_was_given_unchanged():
    """Check that dedup returns a new list and does not edit its argument."""
    names = ["git", "git"]

    dedup(names)

    assert names == ["git", "git"]
