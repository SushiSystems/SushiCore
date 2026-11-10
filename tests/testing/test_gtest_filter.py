# test_gtest_filter.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests narrowing a shard's GoogleTest filter by the caller's."""

import fnmatch

import pytest

from sushicore.testing.gtest_filter import intersect_filters

pytestmark = pytest.mark.small

K_SIZE = "Small_*:*/Small_*"
K_NAMES = ["Small_Rect.Area", "Small_Rect.Scale", "Medium_Rect.Area", "Inst/Small_Rect.Area/0",
           "Inst/Medium_Rect.Area/0", "Small_Slow.Case", "Small_Foo.Bar"]


def _selected(text, name):
    positive, _, negative = text.partition("-")

    def matches(patterns):
        return any(fnmatch.fnmatchcase(name, pattern) for pattern in patterns.split(":") if pattern)

    return matches(positive or "*") and not matches(negative)


def _both(size, user):
    joined = intersect_filters(size, user)
    return [] if joined is None else [name for name in K_NAMES if _selected(joined, name)]


@pytest.mark.parametrize("user", ["Small_Rect.*", "*Rect*", "*.Area", "?mall_Rect.Area", "*", "Medium_*",
                                  "Small_Rect.Area:Medium_Rect.Area", "*/*Area/*", "Rect*", "-Small_Rect.Scale"])
def test_the_joined_filter_selects_exactly_the_cases_both_filters_select(user):
    expected = [name for name in K_NAMES if _selected(K_SIZE, name) and _selected(user, name)]
    assert _both(K_SIZE, user) == expected


def test_a_user_filter_of_another_size_leaves_no_case_and_no_filter():
    assert intersect_filters("Small_*", "Medium_*") is None


def test_no_user_filter_keeps_the_size_filter():
    assert intersect_filters(K_SIZE, "") == K_SIZE


def test_the_negative_patterns_of_both_filters_are_kept():
    joined = intersect_filters("Small_*-Small_Slow.*", "*Rect*-*Scale")
    assert joined.endswith("-Small_Slow.*:*Scale")
    assert _both("Small_*-Small_Slow.*", "*Slow*") == []


def test_a_user_filter_with_a_suite_inside_the_size_keeps_the_users_pattern():
    assert intersect_filters("Small_*", "Small_Rect.*") == "Small_Rect.*"
