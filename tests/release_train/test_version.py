# test_version.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the release version."""

import pytest

from sushicore.release_train.errors import ReleaseTrainError
from sushicore.release_train.version import Version

pytestmark = pytest.mark.small


def test_a_tag_and_a_bare_number_parse_alike():
    assert Version.parse("v0.7.1") == Version.parse("0.7.1") == Version(0, 7, 1)


def test_each_part_raises_and_clears_the_parts_after_it():
    version = Version(1, 2, 3)
    assert [str(version.next(part)) for part in ("patch", "minor", "major")] == ["1.2.4", "1.3.0", "2.0.0"]


def test_a_bad_version_or_part_raises():
    with pytest.raises(ReleaseTrainError):
        Version.parse("1.2")
    with pytest.raises(ReleaseTrainError):
        Version(1, 2, 3).next("build")


def test_the_tag_carries_a_v():
    assert Version(0, 5, 2).tag == "v0.5.2"
