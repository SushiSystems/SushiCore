# test_package_store.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests for the store of built packages."""

from __future__ import annotations

import os

import pytest

from sushicore.provision.sushi_packages.package_error import PackageError
from sushicore.provision.sushi_packages.package_store import PackageStore

from .package_fakes import Clock, install, make_key

pytestmark = pytest.mark.medium


@pytest.fixture
def clock():
    """Return a clock that tests move by hand."""
    return Clock()


@pytest.fixture
def store(tmp_path, clock):
    """Return a store that keeps two packages per library."""
    return PackageStore(tmp_path / "packages", keep=2, clock=clock, sleep=lambda _s: None)


def _install_three(store, clock, name="sushiruntime"):
    """Install three keys of *name* a minute apart and return them oldest first."""
    keys = []
    for index in range(3):
        key = make_key(name, source=f"s{index}")
        install(store, key)
        keys.append(key)
        clock.now += 60
    return keys


def test_a_folder_without_a_stamp_is_not_found(store):
    """Check that an interrupted install is not a package."""
    key = make_key()
    store.stage(key)
    assert store.find(key) is None


def test_a_committed_package_is_found(store):
    """Check that a package is found by its key once it is committed."""
    key = make_key()
    install(store, key)
    assert store.find(key).digest == key.digest()


def test_a_commit_without_an_install_raises(store):
    """Check that committing an empty stage is refused."""
    key = make_key()
    store.discard(key)
    with pytest.raises(PackageError, match="nothing was installed"):
        store.commit(key, 0.0)


def test_the_rename_is_tried_again(store, monkeypatch):
    """Check that a rename that fails once is tried a second time."""
    key = make_key()
    store.stage(key).mkdir()
    real, calls = os.replace, []

    def flaky(source, destination):
        """Fail on the first call, then rename."""
        calls.append(source)
        if len(calls) == 1:
            raise PermissionError("scanner")
        real(source, destination)

    monkeypatch.setattr(os, "replace", flaky)
    assert store.commit(key, 0.0).digest == key.digest()
    assert len(calls) == 2


def test_prune_keeps_the_most_recently_chosen(store, clock):
    """Check that the oldest by last use goes when three exist and two are kept."""
    keys = _install_three(store, clock)
    assert store.prune("sushiruntime") == [keys[0].digest()]


def test_touching_a_package_saves_it_from_prune(store, clock):
    """Check that choosing the oldest package again makes the next one the oldest."""
    keys = _install_three(store, clock)
    store.touch(store.find(keys[0]))
    assert store.prune("sushiruntime") == [keys[1].digest()]


def test_prune_never_removes_a_protected_digest(store, clock):
    """Check that a digest in protect stays even when it is the oldest."""
    keys = _install_three(store, clock)
    assert store.prune("sushiruntime", protect={keys[0].digest()}) == []


def test_prune_never_removes_a_digest_a_package_below_lists(store, clock):
    """Check that a package of another library listing a digest keeps it."""
    keys = _install_three(store, clock)
    install(store, make_key("sushiblas", below=(("sushiruntime", keys[0].digest()),)))
    assert store.prune("sushiruntime") == []


def test_a_deletion_goes_through_trash(store, clock, monkeypatch):
    """Check that a package is renamed to .trash before it is deleted."""
    keys = _install_three(store, clock)
    renamed = []
    real = os.replace

    def record(source, destination):
        """Remember the destination, then rename."""
        renamed.append(str(destination))
        real(source, destination)

    monkeypatch.setattr(os, "replace", record)
    store.prune("sushiruntime")
    assert renamed and renamed[0].endswith(keys[0].digest() + ".trash")


def test_a_rename_that_fails_is_skipped_with_a_warning(tmp_path, clock, monkeypatch):
    """Check that a package that cannot be moved stays, and one warning says so."""
    warnings = []
    store = PackageStore(tmp_path / "packages", keep=2, clock=clock, warn=warnings.append)
    keys = _install_three(store, clock)

    def locked(_source, _destination):
        """Refuse every rename, as a folder an open file holds is refused."""
        raise PermissionError("in use")

    monkeypatch.setattr(os, "replace", locked)
    assert store.prune("sushiruntime") == []
    assert len(warnings) == 1
    assert store.find(keys[0]) is not None


def test_a_fresh_partial_of_another_process_is_left_and_a_stale_one_goes(store, tmp_path, clock):
    """Check that only a partial folder older than a day is removed."""
    install(store, make_key())
    library = tmp_path / "packages" / "sushiruntime"
    fresh, stale = library / "fresh.partial", library / "stale.partial"
    for folder in (fresh, stale):
        folder.mkdir()
    old = clock.now - 2 * 24 * 3600
    os.utime(stale, (old, old))
    os.utime(fresh, (clock.now, clock.now))
    store.prune("sushiruntime")
    assert fresh.exists() and not stale.exists()


def test_a_keep_below_one_raises(tmp_path):
    """Check that a store that keeps nothing is refused."""
    with pytest.raises(PackageError, match="at least one"):
        PackageStore(tmp_path, keep=0)
