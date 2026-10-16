# test_sushi_sources.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests for the order a Sushi library's checkout is looked for in."""

from __future__ import annotations

import pytest

from sushicore.provision import home
from sushicore.provision.sushi_sources import (
    SourceKind,
    directory_variable,
    fetched_dir,
    resolve,
)

pytestmark = pytest.mark.medium


@pytest.fixture
def root(tmp_path, provision_home, monkeypatch):
    """Return a consumer checkout with nothing beside it."""
    monkeypatch.delenv("SUSHILOG_DIR", raising=False)
    checkout = tmp_path / "ws" / "sushiruntime"
    checkout.mkdir(parents=True)
    return checkout


def test_the_directory_variable_is_upper_case():
    """Check that the variable of sushilog is SUSHILOG_DIR."""
    assert directory_variable("sushilog") == "SUSHILOG_DIR"


def test_the_fetched_copy_sits_under_the_home(root):
    """Check that the fetched copy is <home>/sources/<name>/<version>."""
    assert fetched_dir("sushilog", "v1.0.0") == home.root() / "sources" / "sushilog" / "v1.0.0"


def test_nothing_resolves_without_a_checkout(root):
    """Check that resolution is None when no source exists."""
    assert resolve(root, "sushilog", "v1.0.0") is None


def test_the_fetched_copy_is_found_last(root):
    """Check that a fetched copy resolves as fetched."""
    fetched_dir("sushilog", "v1.0.0").mkdir(parents=True)
    assert resolve(root, "sushilog", "v1.0.0").kind is SourceKind.FETCHED


def test_the_fetched_copy_needs_a_version(root):
    """Check that without a version the fetched copy is not looked for."""
    fetched_dir("sushilog", "v1.0.0").mkdir(parents=True)
    assert resolve(root, "sushilog") is None


def test_a_sibling_wins_over_the_fetched_copy(root):
    """Check that ../<name> wins over the fetched copy."""
    fetched_dir("sushilog", "v1.0.0").mkdir(parents=True)
    (root.parent / "sushilog").mkdir()
    found = resolve(root, "sushilog", "v1.0.0")
    assert found.kind is SourceKind.SIBLING and found.path == (root.parent / "sushilog").resolve()


def test_a_configured_directory_wins_over_the_environment_and_the_sibling(
        root, tmp_path, monkeypatch):
    """Check that the configured directory beats the variable, which beats the sibling."""
    (root.parent / "sushilog").mkdir()
    from_env = tmp_path / "env"
    from_env.mkdir()
    configured = tmp_path / "configured"
    configured.mkdir()
    monkeypatch.setenv("SUSHILOG_DIR", str(from_env))

    assert resolve(root, "sushilog", "v1.0.0").path == from_env.resolve()
    found = resolve(root, "sushilog", "v1.0.0", str(configured))
    assert found.kind is SourceKind.DIRECTORY and found.path == configured.resolve()


def test_a_directory_that_does_not_exist_falls_through(root, tmp_path, monkeypatch):
    """Check that a SUSHILOG_DIR naming no folder gives way to the sibling."""
    (root.parent / "sushilog").mkdir()
    monkeypatch.setenv("SUSHILOG_DIR", str(tmp_path / "absent"))
    assert resolve(root, "sushilog", "v1.0.0").kind is SourceKind.SIBLING
