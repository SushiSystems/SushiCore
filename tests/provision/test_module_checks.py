# test_module_checks.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests for the assembly of a module's doctor rows."""

from __future__ import annotations

import pytest

from sushicore.deps_fragment import read
from sushicore.provision import module_checks, probe
from sushicore.provision.config import ProvisionSettings
from sushicore.provision.fragments import TomlDependencySource
from sushicore.provision.module_checks import ModuleState, doctor_checks

from .sushi_fakes import FakeGit, write_fragment

pytestmark = pytest.mark.medium


def _state(root, own):
    """Return the state of the module at *root* whose fragment is *own*."""
    return ModuleState(cfg=ProvisionSettings(platform="linux"), root=root, owner="sushiai",
                       program="sa", own=own, source=TomlDependencySource([]), missing=())


@pytest.fixture
def quiet(monkeypatch):
    """Skip the machine's real tool and toolchain probes."""
    monkeypatch.setattr(module_checks, "standard_checks", lambda cfg, fix: [])
    monkeypatch.setattr(probe, "toolchain_status", lambda cfg, gpu: [])


def test_no_fragment_adds_no_sushi_rows(tmp_path, provision_home, quiet):
    """Check that a module with no fragment gets the stock rows only."""
    names = [check.name for check in doctor_checks(_state(tmp_path, None), [], FakeGit())]
    assert not any(name.startswith("sushi") for name in names)


def test_pinned_and_unpinned_modules_each_get_a_row_and_pins_a_conflict_row(
        tmp_path, provision_home, quiet):
    """Check one row per pin, one per unpinned module, and the conflict row."""
    root = tmp_path / "ws" / "sushiai"
    path = write_fragment(root, {"sushilog": "v1.0.0"})
    path.write_text(path.read_text(encoding="utf-8").replace(
        'depends_on = ["sushilog"]', 'depends_on = ["sushilog", "sushiruntime"]'),
        encoding="utf-8")

    names = [check.name for check in doctor_checks(_state(root, read(path)), [], FakeGit())]

    assert {"sushi sushilog", "sushi sushiruntime", "sushi pins"} <= set(names)
