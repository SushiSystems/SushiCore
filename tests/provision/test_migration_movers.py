# test_migration_movers.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the movers that take a component to the new root, on real temporary trees."""

from __future__ import annotations

import shutil
import os
from pathlib import Path

import pytest

from sushicore.provision.links import is_dir_link, make_dir_link
from sushicore.provision.migrate import migrate
from sushicore.provision.migration_error import MigrationError
from sushicore.provision.migration_plan import plan

from .migration_fakes import aside, copying, snapshot, steps


@pytest.mark.medium
def test_verify_failure_stops_before_the_swap_and_leaves_old_untouched(roots):
    """Check that a copy that differs stops the run with the old tree as it was."""
    old, new = roots
    before = snapshot(old)
    with pytest.raises(MigrationError, match="toolchains"):
        migrate(copying(old, new), lambda _line: None, verify=lambda _source, _copy: False)
    assert not is_dir_link(old)
    assert snapshot(old) == before
    assert not aside(old).exists()
    assert not (new / "toolchains").exists()


@pytest.mark.medium
def test_copy_with_a_missing_file_fails_verification(roots, monkeypatch):
    """Check that a copy that lost a file is told apart from its source."""
    old, new = roots
    real_copytree = shutil.copytree

    def lossy(source, target, *args, **kwargs):
        """Copy the tree and then delete one file of the copy."""
        real_copytree(source, target, *args, **kwargs)
        for path in Path(target).rglob("*.exe"):
            path.unlink()

    monkeypatch.setattr(shutil, "copytree", lossy)
    with pytest.raises(MigrationError, match="differs"):
        migrate(copying(old, new), lambda _line: None)
    assert not is_dir_link(old)


@pytest.mark.medium
def test_unreadable_file_stops_the_copy_before_the_swap(roots, monkeypatch):
    """Check that a file the copy cannot read stops the run and leaves no partial copy."""
    old, new = roots

    def failing(source, target, *args, **kwargs):
        """Stand in for a copy that meets a locked file."""
        Path(target).mkdir()
        raise shutil.Error([(str(source), str(target), "locked")])

    monkeypatch.setattr(shutil, "copytree", failing)
    with pytest.raises(MigrationError, match="could not be copied"):
        migrate(copying(old, new), lambda _line: None)
    assert not is_dir_link(old)
    assert not list(new.glob("*.partial"))


@pytest.mark.medium
def test_rename_of_a_component_in_use_names_it_and_keeps_the_journal(roots, monkeypatch):
    """Check that a rename refused for an open file names the component and the cause."""
    old, new = roots
    real_rename = os.rename

    def rename(source, target):
        """Refuse to move vcpkg, as Windows does while a file in it is open."""
        if Path(source).name == "vcpkg":
            raise PermissionError(13, "The process cannot access the file", str(source))
        real_rename(source, target)

    monkeypatch.setattr(os, "rename", rename)
    with pytest.raises(MigrationError, match="vcpkg: a process still uses"):
        migrate(plan(old, new), lambda _line: None)
    assert steps(new) == [("moved", "toolchains"), ("moved", "tools")]
    assert not is_dir_link(old)
    assert (old / "vcpkg/installed/x.lib").is_file()


@pytest.mark.medium
def test_copy_recreates_a_link_inside_a_component(roots):
    """Check that a directory link inside a component is copied as a link and counted once."""
    old, new = roots
    make_dir_link(old / "vcpkg" / "current", old / "vcpkg" / "installed")
    found = copying(old, new)
    assert next(m for m in found.moves if m.name == "vcpkg").files == 2
    migrate(found, lambda _line: None)
    assert is_dir_link(new / "vcpkg" / "current")
    assert (new / "vcpkg" / "current" / "x.lib").read_bytes() == b"library"
