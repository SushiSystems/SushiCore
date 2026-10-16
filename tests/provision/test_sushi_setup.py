# test_sushi_setup.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests for preparing a module's pinned Sushi libraries before setup reads its closure."""

from __future__ import annotations

import pytest

from sushicore.deps_fragment import pins_at
from sushicore.provision import sushi_setup
from sushicore.provision.config import ProvisionSettings
from sushicore.provision.pipeline import InstallContext

from .sushi_fakes import FakeGit, write_fragment

pytestmark = pytest.mark.medium


def _ctx(consumer="sushiai"):
    """Return a context for a real run by *consumer*."""
    return InstallContext(cfg=ProvisionSettings(platform="linux"), consumer=consumer)


def test_the_locator_tries_the_base_first_then_the_fetched_copy(
        tmp_path, provision_home, monkeypatch):
    """Check that the locator falls back to the fetched copy of a pinned library only."""
    monkeypatch.delenv("SUSHILOG_DIR", raising=False)
    root = tmp_path / "ws" / "sushiai"
    pins = pins_at(write_fragment(root, {"sushilog": "v1.0.0"}))
    fetched = provision_home / "sources" / "sushilog" / "v1.0.0"
    fetched.mkdir(parents=True)

    assert sushi_setup.locator(lambda name: tmp_path, root, pins)("sushilog") == tmp_path
    assert sushi_setup.locator(lambda name: None, root, pins)("sushilog") == fetched.resolve()
    assert sushi_setup.locator(lambda name: None, root, [])("sushilog") is None


def test_prepare_fetches_a_chain_that_agrees(tmp_path, provision_home, recording_console):
    """Check that prepare clones the missing pin and succeeds."""
    root = tmp_path / "ws" / "sushiai"
    write_fragment(root, {"sushilog": "v1.0.0"})
    pins = pins_at(root / "cli/sushistack.deps.toml")
    git = FakeGit()

    assert sushi_setup.prepare(_ctx(), root, pins, git, timeout=1.0)
    assert len(git.calls) == 1


def test_prepare_stops_on_a_conflict_before_cloning(tmp_path, provision_home, recording_console):
    """Check that a conflicting chain fails prepare with no clone."""
    ws = tmp_path / "ws"
    root = ws / "sushiai"
    write_fragment(root, {"sushiruntime": "v3.0.0", "sushilog": "v1.0.0"})
    write_fragment(ws / "sushiruntime", {"sushilog": "v1.1.0"})
    pins = pins_at(root / "cli/sushistack.deps.toml")
    git = FakeGit()

    assert not sushi_setup.prepare(_ctx(), root, pins, git, timeout=1.0)
    assert git.calls == []
    errors = [args[0] for name, args in recording_console.calls if name == "error"]
    assert any("sushiai" in e and "sushiruntime" in e for e in errors)


def test_prepare_has_nothing_to_do_without_pins(tmp_path, provision_home):
    """Check that a module with no pins takes no lock and succeeds."""
    assert sushi_setup.prepare(_ctx(), tmp_path, [], FakeGit(), timeout=1.0)
    assert not (provision_home / ".lock").exists()
