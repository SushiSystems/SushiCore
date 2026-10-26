# test_stable_link.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests for the per-consumer link to a package."""

from __future__ import annotations

import os

import pytest

from sushicore.provision.sushi_packages.stable_link import StableLink

pytestmark = pytest.mark.medium


@pytest.fixture
def folders(tmp_path):
    """Return the packages root and two package folders of one library."""
    root = tmp_path / "packages"
    first, second = root / "sushiruntime" / "d1", root / "sushiruntime" / "d2"
    first.mkdir(parents=True)
    second.mkdir()
    return root, first, second


def _symlinks_work(tmp_path) -> bool:
    """Report whether this process may create a symlink."""
    try:
        os.symlink(tmp_path, tmp_path / "probe", target_is_directory=True)
    except OSError:
        return False
    return True


def test_the_windows_link_follows_the_newest_package(folders):
    """Check that two junction updates leave the link on the second package and keep both."""
    root, first, second = folders
    link = StableLink(root, windows=True)
    link.point("sushiruntime", "c1", "sushiai", first)
    path = link.point("sushiruntime", "c1", "sushiai", second)
    assert path.resolve() == second.resolve()
    assert first.is_dir() and second.is_dir()


def test_the_posix_link_is_replaced_beside_the_old_one(folders, tmp_path):
    """Check that the symlink is swapped by rename and leaves no .new file."""
    if not _symlinks_work(tmp_path):
        pytest.skip("this account may not create symlinks")
    root, first, second = folders
    link = StableLink(root, windows=False)
    link.point("sushiruntime", "c1", "sushiai", first)
    path = link.point("sushiruntime", "c1", "sushiai", second)
    assert path.resolve() == second.resolve()
    assert not (path.parent / (path.name + ".new")).exists()


def test_the_name_has_config_and_consumer(folders):
    """Check the shape of the link name."""
    root, _, _ = folders
    assert StableLink(root).path("sushiruntime", "c1", "sushiai").name == "@c1-sushiai"


def test_targets_lists_every_digest_a_link_names(folders):
    """Check that the links of two consumers give two digests."""
    root, first, second = folders
    link = StableLink(root, windows=True)
    link.point("sushiruntime", "c1", "sushiai", first)
    link.point("sushiruntime", "c1", "sushiengine", second)
    assert link.targets("sushiruntime") == {"d1", "d2"}


def test_targets_of_an_unknown_library_is_empty(folders):
    """Check that a library with no folder has no targets."""
    root, _, _ = folders
    assert StableLink(root).targets("sushilog") == set()
