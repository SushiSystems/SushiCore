# test_checkout_finder.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests how the SushiCore checkout is found."""

from __future__ import annotations

import pytest

from sushicore.shared_tools import CheckoutNotFoundError, find_checkout

pytestmark = pytest.mark.medium


def test_an_explicit_directory_wins(tmp_path):
    """The path given with --from is used as it is."""
    assert find_checkout(tmp_path / "root", "v1", tmp_path) == tmp_path


def test_an_explicit_path_that_is_no_directory_raises(tmp_path):
    """A --from that does not exist is an error, not a fall back."""
    with pytest.raises(CheckoutNotFoundError):
        find_checkout(tmp_path, "v1", tmp_path / "none")


def test_the_sibling_is_found_beside_the_root(tmp_path):
    """The folder ../sushicore of the root is the checkout."""
    (tmp_path / "sushicore").mkdir()
    (tmp_path / "repo").mkdir()
    assert find_checkout(tmp_path / "repo", "v1").samefile(tmp_path / "sushicore")


def test_no_checkout_raises(tmp_path, monkeypatch):
    """Without a sibling or a fetched copy the finder says so."""
    monkeypatch.delenv("SUSHICORE_DIR", raising=False)
    (tmp_path / "repo").mkdir()
    with pytest.raises(CheckoutNotFoundError):
        find_checkout(tmp_path / "repo", "v1")
