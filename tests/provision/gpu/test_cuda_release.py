# test_cuda_release.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""A release's version reads and prints as NVIDIA spells it."""

from __future__ import annotations

import pytest

from sushicore.provision.gpu.cuda_release import format_version, parse_version


pytestmark = pytest.mark.small


def test_versions_round_trip_through_text():
    """Check that parsing and formatting are inverse."""
    assert format_version(parse_version("13.1.2")) == "13.1.2"


def test_a_version_that_is_not_digits_raises():
    """Check that a label with letters is refused."""
    with pytest.raises(ValueError):
        parse_version("13.x")
