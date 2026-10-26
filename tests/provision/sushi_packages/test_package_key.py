# test_package_key.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests for the key that names a built package."""

from __future__ import annotations

import dataclasses

import pytest

from sushicore.provision.sushi_packages.package_key import PackageKey

pytestmark = pytest.mark.small


def _key(**changes) -> PackageKey:
    """Return a key with every part set, then *changes* applied."""
    base = PackageKey("sushiruntime", "src1", "tc1", "release", "lean-1", "in1",
                      ("--distributed",), (("sushilog", "aa"), ("sushiprofiler", "bb")))
    return dataclasses.replace(base, **changes)


def test_equal_parts_give_one_digest():
    """Check that two keys with equal parts have one digest."""
    assert _key().digest() == _key().digest()


@pytest.mark.parametrize("changes", [
    {"name": "sushiblas"},
    {"source": "src2"},
    {"toolchain": "tc2"},
    {"build_type": "debug"},
    {"recipe": "lean-2"},
    {"inputs": "in2"},
    {"options": ()},
    {"below": (("sushilog", "cc"),)},
])
def test_each_part_changes_the_digest(changes):
    """Check that changing any one part gives another digest."""
    assert _key(**changes).digest() != _key().digest()


def test_the_order_of_below_does_not_matter():
    """Check that the digest does not depend on the order of the packages below."""
    swapped = _key(below=(("sushiprofiler", "bb"), ("sushilog", "aa")))
    assert swapped.digest() == _key().digest()


def test_the_short_form_is_the_head_of_the_digest():
    """Check that the short form is the first 12 hex digits."""
    assert _key().short() == _key().digest()[:12]
