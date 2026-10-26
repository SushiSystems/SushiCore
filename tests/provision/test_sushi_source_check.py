# test_sushi_source_check.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests for the doctor checks of pinned Sushi libraries."""

from __future__ import annotations

import pytest

from sushicore.deps_fragment import SushiPin, read
from sushicore.provision.doctor import State
from sushicore.provision.sushi_source_check import (
    pin_conflict_check,
    sushi_source_check,
    unpinned_check,
)
from sushicore.provision.sushi_sources import fetched_dir

from .sushi_fakes import K_OTHER, K_PINNED, FakeGit, write_fragment

pytestmark = pytest.mark.medium

K_PIN = SushiPin("sushilog", "v1.0.0", K_PINNED)


@pytest.fixture
def root(tmp_path, provision_home, monkeypatch):
    """Return a consumer checkout with nothing beside it."""
    monkeypatch.delenv("SUSHILOG_DIR", raising=False)
    checkout = tmp_path / "ws" / "sushiruntime"
    checkout.mkdir(parents=True)
    return checkout


def test_a_missing_library_fails_with_the_fix(root):
    """Check that no checkout fails and names setup as the fix."""
    result = sushi_source_check(root, K_PIN, FakeGit(), "sr setup").run()
    assert result.state is State.FAIL and result.fix == "sr setup"


def test_a_fetched_library_reports_fetched(root):
    """Check that the fetched copy is named as the source."""
    fetched_dir("sushilog", "v1.0.0").mkdir(parents=True)
    result = sushi_source_check(root, K_PIN, FakeGit(), "sr setup").run()
    assert result.state is State.OK and result.detail.startswith("fetched")


def test_a_sibling_at_the_pin_reports_sibling(root):
    """Check that a sibling at the pinned commit passes."""
    sibling = root.parent / "sushilog"
    sibling.mkdir()
    git = FakeGit(heads={sibling: K_PINNED})
    result = sushi_source_check(root, K_PIN, git, "sr setup").run()
    assert result.state is State.OK and result.detail.startswith("sibling")


def test_a_sibling_off_the_pin_warns(root):
    """Check that a sibling at another commit warns and names both commits."""
    sibling = root.parent / "sushilog"
    sibling.mkdir()
    git = FakeGit(heads={sibling: K_OTHER})
    result = sushi_source_check(root, K_PIN, git, "sr setup").run()
    assert result.state is State.WARN
    assert K_OTHER in result.detail and K_PINNED in result.detail


def test_the_pin_check_fails_on_a_conflict_and_passes_without_one(tmp_path, provision_home):
    """Check that the pin check fails naming both pinners, and passes when they agree."""
    ws = tmp_path / "ws"
    root = ws / "sushiblas"
    write_fragment(root, {"sushiruntime": "v3.0.0", "sushilog": "v1.0.0"})
    runtime = write_fragment(ws / "sushiruntime", {"sushilog": "v1.1.0"})
    (ws / "sushilog").mkdir()
    pins = read(root / "cli" / "sushistack.deps.toml").pins

    failed = pin_conflict_check("sushiblas", root, pins).run()
    assert failed.state is State.FAIL
    assert "sushiblas" in failed.detail and "sushiruntime" in failed.detail

    write_fragment(ws / "sushiruntime", {"sushilog": "v1.0.0"})
    assert runtime.is_file()
    assert pin_conflict_check("sushiblas", root, pins).run().state is State.OK


def test_an_unpinned_module_warns_and_names_where_it_was_found(root):
    """Check that an unpinned module warns, naming its sibling, and is not required."""
    (root.parent / "sushilog").mkdir()
    check = unpinned_check(root, "sushilog")
    result = check.run()
    assert not check.required
    assert result.state is State.WARN
    assert result.detail.startswith("not pinned; pin it in [sushisystems.sushilog]")
    assert "sibling" in result.detail
