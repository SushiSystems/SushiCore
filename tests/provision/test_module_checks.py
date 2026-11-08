# test_module_checks.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the assembly of a module's doctor rows."""

from __future__ import annotations

import pytest

from sushicore.deps_fragment import read
from sushicore.provision.config import ProvisionSettings
from sushicore.provision.fragments import TomlDependencySource
from sushicore.provision.module_checks import ModuleState, doctor_checks

from .sushi_fakes import pinned_git, write_fragment



def _state(root, own):
    """Return the state of the module at *root* whose fragment is *own*."""
    return ModuleState(cfg=ProvisionSettings(platform="linux"), root=root, owner="sushiai",
                       program="sa", own=own, source=TomlDependencySource([]), missing=())


def _names(root, own):
    """Return the names of the doctor rows of the module at *root* whose fragment is *own*."""
    rows = doctor_checks(_state(root, own), [], pinned_git(),
                         base_checks=lambda cfg, fix: [], presence={})
    return [check.name for check in rows]


def _fragment_with_an_unpinned_module(root):
    """Write a fragment pinning sushilog and naming sushiruntime without a pin; return it read."""
    path = write_fragment(root, {"sushilog": "v1.0.0"})
    path.write_text(path.read_text(encoding="utf-8").replace(
        'depends_on = ["sushilog"]', 'depends_on = ["sushilog", "sushiruntime"]'),
        encoding="utf-8")
    return read(path)


@pytest.mark.medium
def test_no_fragment_adds_no_sushi_rows(tmp_path, provision_home):
    """Check that a module with no fragment gets the stock rows only."""
    assert not any(name.startswith("sushi") for name in _names(tmp_path, None))


@pytest.mark.medium
def test_a_pinned_module_gets_a_row(tmp_path, provision_home):
    """Check that a module the fragment pins gets a row."""
    root = tmp_path / "ws" / "sushiai"
    assert "sushi sushilog" in _names(root, _fragment_with_an_unpinned_module(root))


@pytest.mark.medium
def test_an_unpinned_module_gets_a_row(tmp_path, provision_home):
    """Check that a module the fragment names without a pin gets a row."""
    root = tmp_path / "ws" / "sushiai"
    assert "sushi sushiruntime" in _names(root, _fragment_with_an_unpinned_module(root))


@pytest.mark.medium
def test_the_pins_get_a_conflict_row(tmp_path, provision_home):
    """Check that the pins of a fragment get one conflict row."""
    root = tmp_path / "ws" / "sushiai"
    assert "sushi pins" in _names(root, _fragment_with_an_unpinned_module(root))
