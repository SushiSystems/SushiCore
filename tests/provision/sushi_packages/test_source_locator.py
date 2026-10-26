# test_source_locator.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests for the checkout locator of the package walk."""

from __future__ import annotations

import pytest

from sushicore.provision.sushi_packages.package_error import PackageError
from sushicore.provision.sushi_packages.source_locator import SushiSourceLocator

pytestmark = pytest.mark.medium


@pytest.fixture
def root(tmp_path, provision_home, monkeypatch):
    """Return a consumer checkout with nothing beside it."""
    monkeypatch.delenv("SUSHILOG_DIR", raising=False)
    checkout = tmp_path / "ws" / "sushiai"
    checkout.mkdir(parents=True)
    return checkout


def test_the_configured_directory_wins_over_the_sibling(root, tmp_path):
    """Check that a configured directory is found before the sibling."""
    (root.parent / "sushilog").mkdir()
    explicit = tmp_path / "elsewhere"
    explicit.mkdir()
    assert SushiSourceLocator().locate(root, "sushilog", "", str(explicit)) == explicit.resolve()


def test_the_sibling_is_found(root):
    """Check that ../<name> is found when nothing is configured."""
    (root.parent / "sushilog").mkdir()
    found = SushiSourceLocator().locate(root, "sushilog", "", "")
    assert found == (root.parent / "sushilog").resolve()


def test_no_checkout_raises_naming_the_directory_variable(root):
    """Check that a library with no checkout is refused naming <NAME>_DIR."""
    with pytest.raises(PackageError, match="SUSHILOG_DIR"):
        SushiSourceLocator().locate(root, "sushilog", "v1.0.0", "")
