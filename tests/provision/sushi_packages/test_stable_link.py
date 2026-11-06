# test_stable_link.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the per-consumer link to a package."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from sushicore.provision import links
from sushicore.provision.sushi_packages.stable_link import StableLink


def _symlinks_work() -> bool:
    """Report whether this process may create a symlink."""
    with tempfile.TemporaryDirectory() as folder:
        try:
            os.symlink(folder, Path(folder) / "probe", target_is_directory=True)
        except OSError:
            return False
    return True


#: Skips a test on a platform or account that cannot make a symlink.
K_NEEDS_SYMLINKS = pytest.mark.skipif(
    os.name == "nt" or not _symlinks_work(), reason="this platform or account makes no symlink")


@pytest.fixture
def folders(tmp_path):
    """Return the packages root and two package folders of one library."""
    root = tmp_path / "packages"
    first, second = root / "sushiruntime" / "d1", root / "sushiruntime" / "d2"
    first.mkdir(parents=True)
    second.mkdir()
    return root, first, second


@pytest.mark.medium
def test_the_windows_link_follows_the_newest_package(folders):
    """Check that two junction updates leave the link on the second package."""
    root, first, second = folders
    link = StableLink(root, windows=True)
    link.point("sushiruntime", "c1", "sushiai", first)
    path = link.point("sushiruntime", "c1", "sushiai", second)
    assert path.resolve() == second.resolve()


@pytest.mark.medium
def test_the_windows_link_update_keeps_every_package_folder(folders):
    """Check that moving the junction deletes no package folder."""
    root, first, second = folders
    link = StableLink(root, windows=True)
    link.point("sushiruntime", "c1", "sushiai", first)
    link.point("sushiruntime", "c1", "sushiai", second)
    assert (first.is_dir(), second.is_dir()) == (True, True)


@pytest.mark.medium
@K_NEEDS_SYMLINKS
def test_the_posix_link_is_replaced_beside_the_old_one(folders):
    """Check that the symlink swapped by rename names the second package."""
    root, first, second = folders
    link = StableLink(root, windows=False)
    link.point("sushiruntime", "c1", "sushiai", first)
    path = link.point("sushiruntime", "c1", "sushiai", second)
    assert path.resolve() == second.resolve()


@pytest.mark.medium
@K_NEEDS_SYMLINKS
def test_the_posix_link_update_leaves_no_new_file(folders):
    """Check that the swap leaves no .new file beside the link."""
    root, first, second = folders
    link = StableLink(root, windows=False)
    link.point("sushiruntime", "c1", "sushiai", first)
    path = link.point("sushiruntime", "c1", "sushiai", second)
    assert not (path.parent / (path.name + ".new")).exists()


@pytest.mark.small
def test_the_name_has_config_and_consumer():
    """Check the shape of the link name."""
    link = StableLink(Path("packages")).path("sushiruntime", "c1", "sushiai")
    assert link.name == "@c1-sushiai"


@pytest.mark.medium
def test_targets_lists_every_digest_a_link_names(folders):
    """Check that the links of two consumers give two digests."""
    root, first, second = folders
    link = StableLink(root, windows=True)
    link.point("sushiruntime", "c1", "sushiai", first)
    link.point("sushiruntime", "c1", "sushiengine", second)
    assert link.targets("sushiruntime") == {"d1", "d2"}


@pytest.mark.medium
def test_targets_counts_only_entries_that_carry_the_link_mark(folders):
    """Check that a link without the mark beside the library's links is not a target."""
    root, first, second = folders
    link = StableLink(root, windows=True)
    link.point("sushiruntime", "c1", "sushiai", first)
    links.make_dir_link(root / "sushiruntime" / "plain", second)
    assert link.targets("sushiruntime") == {"d1"}


@pytest.mark.medium
def test_targets_of_an_unknown_library_is_empty(tmp_path):
    """Check that a library with no folder has no targets."""
    assert StableLink(tmp_path / "packages").targets("sushilog") == set()
