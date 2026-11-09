# test_migration_plan.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the plan of a dependency-root migration, over in-memory disk reads."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.provision.migration_error import MigrationError
from sushicore.provision.migration_plan import PlanProbes, plan


K_OLD = Path("/machine/old")
K_NEW = Path("/machine/new")

#: What the old root holds: each component with the size of its single file.
K_COMPONENTS = {"toolchains": 5, "tools": 12, "vcpkg": 7}


def _probes(**overrides) -> PlanProbes:
    """Return probes for an old root holding the three components, a free new root, one volume."""
    values = dict(
        is_link=lambda path: False,
        link_target=lambda path: None,
        is_dir=lambda path: path == K_OLD,
        present=lambda path: False,
        resolve=lambda path: path,
        subfolders=lambda path: [K_OLD / name for name in K_COMPONENTS],
        file_sizes=lambda path: {"file": K_COMPONENTS[path.name]},
        free_bytes=lambda path: 1000,
        same_volume=lambda old, new: True,
        journal_exists=lambda root: False)
    values.update(overrides)
    return PlanProbes(**values)


@pytest.mark.small
def test_plan_counts_files_and_bytes_per_component():
    """Check that plan counts the files and bytes of each top-level directory."""
    found = plan(K_OLD, K_NEW, _probes())
    assert [(m.name, m.files, m.bytes) for m in found.moves] == [
        ("toolchains", 1, 5), ("tools", 1, 12), ("vcpkg", 1, 7)]
    assert (found.total_bytes, found.moves[0].target) == (24, K_NEW / "toolchains")


@pytest.mark.small
def test_plan_reports_one_volume_for_two_folders_side_by_side():
    """Check that two roots on one volume need no space."""
    found = plan(K_OLD, K_NEW, _probes(free_bytes=lambda path: 0))
    assert found.same_volume
    assert found.enough_space


@pytest.mark.small
def test_plan_reports_a_short_target_volume_when_the_volumes_differ():
    """Check that a copy to another volume with too little space is not enough."""
    found = plan(K_OLD, K_NEW, _probes(same_volume=lambda old, new: False,
                                       free_bytes=lambda path: 10))
    assert not found.enough_space


@pytest.mark.small
def test_plan_rejects_a_name_already_in_the_target():
    """Check that plan refuses when the target holds a component's name."""
    probes = _probes(present=lambda path: path == K_NEW / "vcpkg")
    with pytest.raises(MigrationError, match="vcpkg"):
        plan(K_OLD, K_NEW, probes)


@pytest.mark.small
def test_plan_ignores_lock_and_registry_in_the_target():
    """Check that the lock and the registry of the target are not collisions."""
    probes = _probes(present=lambda path: path.name in (".lock", "registry.toml"))
    assert len(plan(K_OLD, K_NEW, probes).moves) == 3


@pytest.mark.small
def test_plan_rejects_a_target_inside_the_old_root():
    """Check that plan refuses a new root that lies under the old one."""
    with pytest.raises(MigrationError, match="inside"):
        plan(K_OLD, K_OLD / "moved", _probes())


@pytest.mark.small
def test_plan_rejects_a_missing_old_root():
    """Check that plan refuses an old root that does not exist."""
    with pytest.raises(MigrationError, match="not a directory"):
        plan(K_OLD, K_NEW, _probes(is_dir=lambda path: False))


@pytest.mark.small
def test_plan_rejects_an_old_root_linked_elsewhere():
    """Check that plan refuses an old root that links to another directory."""
    other = Path("/machine/other")
    probes = _probes(is_link=lambda path: path == K_OLD,
                     link_target=lambda path: other if path == K_OLD else None)
    with pytest.raises(MigrationError, match="is a link"):
        plan(K_OLD, K_NEW, probes)
