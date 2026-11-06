# test_package_request.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the request a consumer hands the resolver."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.provision.sushi_packages.package_request import PackageRequest

pytestmark = pytest.mark.small


def test_two_requests_do_not_share_their_default_mappings():
    """Check that the default mappings are separate objects."""
    first = PackageRequest("a", Path("."), "c", "release")
    second = PackageRequest("b", Path("."), "c", "release")
    assert first.options is not second.options
