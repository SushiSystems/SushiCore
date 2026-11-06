# test_package_locks.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the lock order of a package build."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.provision.sushi_packages.package_error import PackageError
from sushicore.provision.sushi_packages.package_locks import MemoryLocks, PackageLocks

pytestmark = pytest.mark.small

K_ROOT = Path("packages")


@pytest.fixture
def taken():
    """Return the locks, and the in-memory factory that opens them."""
    factory = MemoryLocks()
    return PackageLocks(K_ROOT, factory=factory), factory


def test_the_lock_files_have_the_documented_names(taken):
    """Check the file names of the checkout, key and link locks."""
    locks, factory = taken
    with locks.checkout("sushiruntime", Path("ws")):
        with locks.key("sushiruntime", "d1"):
            with locks.link("sushiruntime", "Sushi AI"):
                pass
    names = [path.name for path in factory.asked]
    assert names[1:] == ["sushiruntime-d1.lock", "sushiruntime-link-sushi_ai.lock"]
    assert names[0].startswith("sushiruntime-") and names[0].endswith(".lock")


def test_the_order_checkout_key_link_is_allowed(taken):
    """Check that the three locks are held together when taken in order."""
    locks, factory = taken
    with locks.checkout("a", Path("ws")), locks.key("a", "d"), locks.link("a", "c"):
        held = [path.name for path in factory.held]
    assert held[1:] == ["a-d.lock", "a-link-c.lock"]


@pytest.mark.parametrize("first, second", [("key", "checkout"), ("link", "key"),
                                           ("link", "checkout")])
def test_a_lock_of_a_lower_rank_after_a_higher_one_raises(taken, first, second):
    """Check that the reverse order is refused."""
    locks, _ = taken
    take = {"checkout": lambda: locks.checkout("a", Path("ws")),
            "key": lambda: locks.key("a", "d"), "link": lambda: locks.link("a", "c")}
    with take[first]():
        with pytest.raises(PackageError, match="order"):
            take[second]().__enter__()


def test_a_released_lock_lets_a_lower_rank_be_taken_again(taken):
    """Check that a key lock can be taken after a link lock was released."""
    locks, factory = taken
    with locks.link("a", "c"):
        pass
    with locks.key("a", "d"):
        held = [path.name for path in factory.held]
    assert held == ["a-d.lock"]
