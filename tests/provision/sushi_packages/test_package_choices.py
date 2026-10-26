# test_package_choices.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests for the record of which package each library was chosen at."""

from __future__ import annotations

import pytest

from sushicore.provision.sushi_packages.package_choices import PackageChoices
from sushicore.provision.sushi_packages.package_error import PackageConflictError

pytestmark = pytest.mark.small


def test_the_same_digest_twice_is_not_a_conflict():
    """Check that two choosers agreeing on a digest is accepted."""
    choices = PackageChoices()
    choices.add("sushiruntime", "a" * 64, "the source tree")
    choices.add("sushiruntime", "a" * 64, "the sushiblas package")


def test_two_digests_for_one_library_raise_naming_both_and_both_choosers():
    """Check that the message holds both short digests and both owners."""
    choices = PackageChoices()
    choices.add("sushiruntime", "a" * 64, "the source tree")
    with pytest.raises(PackageConflictError) as caught:
        choices.add("sushiruntime", "b" * 64, "SUSHIBLAS_PACKAGE")
    message = str(caught.value)
    assert "a" * 12 in message and "b" * 12 in message
    assert "the source tree" in message and "SUSHIBLAS_PACKAGE" in message


def test_two_libraries_may_hold_different_digests():
    """Check that digests are per library."""
    choices = PackageChoices()
    choices.add("sushilog", "a" * 64, "x")
    choices.add("sushiruntime", "b" * 64, "x")
