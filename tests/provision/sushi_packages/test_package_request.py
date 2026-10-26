# test_package_request.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests for the request a consumer hands the resolver."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.provision.sushi_packages.package_request import PackageRequest

pytestmark = pytest.mark.small


def test_a_request_defaults_to_the_standard_fragment_and_no_choices():
    """Check the defaults of the optional fields."""
    request = PackageRequest("sushiai", Path("."), "clang++", "release")
    assert request.fragment == "cli/sushistack.deps.toml"
    assert (request.options, request.configured, request.vcpkg_root, request.triplet) == (
        {}, {}, None, "")


def test_two_requests_do_not_share_their_default_mappings():
    """Check that the default mappings are separate objects."""
    first = PackageRequest("a", Path("."), "c", "release")
    second = PackageRequest("b", Path("."), "c", "release")
    assert first.options is not second.options
