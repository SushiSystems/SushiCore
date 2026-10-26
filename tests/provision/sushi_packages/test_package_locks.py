# test_package_locks.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests for the lock order of a package build."""

from __future__ import annotations

import contextlib

import pytest

from sushicore.provision.sushi_packages.package_error import PackageError
from sushicore.provision.sushi_packages.package_locks import PackageLocks

pytestmark = pytest.mark.small


@pytest.fixture
def taken(tmp_path):
    """Return the locks, and the list of lock files the factory was asked for."""
    asked = []

    @contextlib.contextmanager
    def factory(path, timeout):
        """Record the lock file and hold nothing."""
        asked.append(path)
        yield

    return PackageLocks(tmp_path / "packages", factory=factory), asked


def test_the_lock_files_have_the_documented_names(taken, tmp_path):
    """Check the file names of the checkout, key and link locks."""
    locks, asked = taken
    with locks.checkout("sushiruntime", tmp_path):
        with locks.key("sushiruntime", "d1"):
            with locks.link("sushiruntime", "Sushi AI"):
                pass
    names = [path.name for path in asked]
    assert names[1:] == ["sushiruntime-d1.lock", "sushiruntime-link-sushi_ai.lock"]
    assert names[0].startswith("sushiruntime-") and names[0].endswith(".lock")


def test_the_order_checkout_key_link_is_allowed(taken, tmp_path):
    """Check that taking the three locks in order raises nothing."""
    locks, _ = taken
    with locks.checkout("a", tmp_path), locks.key("a", "d"), locks.link("a", "c"):
        pass


@pytest.mark.parametrize("first, second", [("key", "checkout"), ("link", "key"),
                                           ("link", "checkout")])
def test_a_lock_of_a_lower_rank_after_a_higher_one_raises(taken, tmp_path, first, second):
    """Check that the reverse order is refused."""
    locks, _ = taken
    take = {"checkout": lambda: locks.checkout("a", tmp_path), "key": lambda: locks.key("a", "d"),
            "link": lambda: locks.link("a", "c")}
    with take[first]():
        with pytest.raises(PackageError, match="order"):
            take[second]().__enter__()


def test_the_held_state_is_cleared_after_a_lock(taken, tmp_path):
    """Check that a key lock can be taken again after a link lock was released."""
    locks, _ = taken
    with locks.link("a", "c"):
        pass
    with locks.key("a", "d"):
        pass
