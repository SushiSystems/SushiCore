# test_sync_service.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests the sync service on a tagged SushiCore checkout and a repository on disk."""

from __future__ import annotations

import shutil

import pytest

from sushicore.shared_tools import K_EXCLUDED, K_LOCK_PATH, GitReader, LocalEditsError, SharedToolsSync, read_lock

from .conftest import K_SHARED, K_TAG

pytestmark = pytest.mark.medium


def _sync(upstream, target, **options):
    """Runs a sync of the tag into the target."""
    return SharedToolsSync(GitReader(upstream), target, K_TAG, **options).run()


def test_sync_writes_the_files_and_the_lock(upstream, target):
    """The lock holds the tag, its commit and a hash for each shared file, and no SushiCore-only file."""
    result = _sync(upstream, target)
    lock = read_lock(target)
    assert lock.tag == K_TAG
    assert len(lock.commit) == 40
    assert K_SHARED in lock.files
    assert ".github/SECURITY.md" in lock.files
    assert not K_EXCLUDED.intersection(lock.files)
    assert K_SHARED in result.written
    assert lock.differing(target) == []


def test_a_local_edit_is_refused_and_nothing_else_is_written(upstream, target):
    """A file holding text no release held stops the sync before any write."""
    _sync(upstream, target)
    edited = target / K_SHARED
    edited.write_text(edited.read_text(encoding="utf-8") + "# mine\n", encoding="utf-8")
    shutil.rmtree(target / "tools" / "documentation")
    with pytest.raises(LocalEditsError) as refused:
        _sync(upstream, target)
    assert refused.value.files == [K_SHARED]
    assert "# mine" in edited.read_text(encoding="utf-8")
    assert not (target / "tools" / "documentation").exists()


def test_force_overwrites_a_local_edit(upstream, target):
    """With force the edited file is brought back to the tag."""
    _sync(upstream, target)
    edited = target / K_SHARED
    edited.write_text(edited.read_text(encoding="utf-8") + "# mine\n", encoding="utf-8")
    _sync(upstream, target, force=True)
    assert "# mine" not in edited.read_text(encoding="utf-8")


def test_kept_files_stay_as_the_repository_holds_them(upstream, target):
    """The settings and README of the repository and a kept file are untouched, and a kept file is not locked."""
    kept = "tools/ci/" + next((upstream / "tools" / "ci").iterdir()).name
    (target / kept).parent.mkdir(parents=True)
    (target / kept).write_text("my own\n", encoding="utf-8")
    _sync(upstream, target, keep=[kept])
    assert (target / "tools" / "settings.py").read_text(encoding="utf-8") == "K_OWN = 1\n"
    assert (target / "tools" / "README.md").read_text(encoding="utf-8") == "own readme\n"
    assert (target / kept).read_text(encoding="utf-8") == "my own\n"
    assert kept not in read_lock(target).files


def test_dry_run_writes_nothing(upstream, target):
    """A dry run lists the files and writes neither them nor the lock."""
    result = _sync(upstream, target, dry_run=True)
    assert K_SHARED in result.written
    assert not (target / K_SHARED).exists()
    assert not (target / K_LOCK_PATH).exists()
