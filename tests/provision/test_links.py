# test_links.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests for directory links."""

from __future__ import annotations

import os

import pytest

from sushicore.provision.links import (
    _is_junction,
    is_dir_link,
    link_target,
    make_dir_link,
    remove_dir_link,
)


def test_link_resolves_to_target_contents(tmp_path):
    """Check that a link shows the target's contents and names the target."""
    target = tmp_path / "new"
    (target / "tools").mkdir(parents=True)
    link = tmp_path / "old"
    make_dir_link(link, target)
    assert is_dir_link(link)
    assert (link / "tools").is_dir()
    assert link_target(link).resolve() == target.resolve()


def test_remove_keeps_target_contents(tmp_path):
    """Check that removing a link leaves the files of its target."""
    target = tmp_path / "new"
    target.mkdir()
    (target / "keep.txt").write_text("x", encoding="utf-8")
    link = tmp_path / "old"
    make_dir_link(link, target)
    remove_dir_link(link)
    assert not link.exists()
    assert (target / "keep.txt").read_text(encoding="utf-8") == "x"


def test_remove_refuses_a_real_directory(tmp_path):
    """Check that a real directory is never removed as a link."""
    real = tmp_path / "real"
    real.mkdir()
    with pytest.raises(ValueError):
        remove_dir_link(real)
    assert real.is_dir()


def test_make_refuses_an_existing_path(tmp_path):
    """Check that a link is not made over a path that exists."""
    (tmp_path / "old").mkdir()
    with pytest.raises(FileExistsError):
        make_dir_link(tmp_path / "old", tmp_path)


def test_plain_directory_is_not_a_link(tmp_path):
    """Check that a plain directory has no link target."""
    assert not is_dir_link(tmp_path)
    assert link_target(tmp_path) is None


def test_missing_path_is_not_a_link(tmp_path):
    """Check that a path that does not exist is not a link."""
    assert not is_dir_link(tmp_path / "absent")
    assert link_target(tmp_path / "absent") is None


def test_link_to_a_removed_target_is_still_a_link(tmp_path):
    """Check that a link whose target is gone is still seen and removable."""
    target = tmp_path / "new"
    target.mkdir()
    link = tmp_path / "old"
    make_dir_link(link, target)
    target.rmdir()
    assert is_dir_link(link)
    remove_dir_link(link)
    assert not is_dir_link(link)


@pytest.mark.skipif(os.name != "nt", reason="junctions exist on Windows only")
def test_junction_is_recognised_by_its_reparse_tag(tmp_path):
    """Check that a junction is told apart from a directory by its reparse tag."""
    target = tmp_path / "new"
    target.mkdir()
    link = tmp_path / "old"
    make_dir_link(link, target)
    assert _is_junction(link)
    assert not _is_junction(target)
    assert not _is_junction(tmp_path / "absent")
