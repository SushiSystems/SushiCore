# test_migration_disk.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for what a migration reads from and does to the disk."""

from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest

from sushicore.provision.migration_disk import aside_path, file_sizes, partial_path, remove_tree


@pytest.mark.medium
def test_file_sizes_lists_every_file_by_its_relative_path(tmp_path):
    """Check that a nested tree is measured file by file under forward-slash paths."""
    (tmp_path / "a" / "b").mkdir(parents=True)
    (tmp_path / "a" / "b" / "x.bin").write_bytes(b"123")
    (tmp_path / "y.bin").write_bytes(b"12345")
    assert file_sizes(tmp_path) == {"a/b/x.bin": 3, "y.bin": 5}


@pytest.mark.medium
def test_remove_tree_deletes_a_tree_with_a_read_only_file(tmp_path):
    """Check that a read-only file does not stop the removal of its folder."""
    folder = tmp_path / "tree"
    folder.mkdir()
    locked = folder / "locked.txt"
    locked.write_text("x", encoding="utf-8")
    os.chmod(locked, stat.S_IREAD)
    remove_tree(folder)
    assert not folder.exists()


@pytest.mark.small
def test_the_aside_and_partial_paths_extend_the_name_beside_it():
    """Check that the set-aside copy and the unverified copy sit beside the original."""
    assert aside_path(Path("/m/old")) == Path("/m/old.pre-migrate")
    assert partial_path(Path("/m/new/tools")) == Path("/m/new/tools.partial")
