# test_link_publisher.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests for the publication of a consumer link."""

from __future__ import annotations

import contextlib

import pytest

from sushicore.provision.sushi_packages.link_publisher import LinkPublisher
from sushicore.provision.sushi_packages.package_locks import PackageLocks
from sushicore.provision.sushi_packages.package_store import PackageStore
from sushicore.provision.sushi_packages.stable_link import StableLink

from .package_fakes import install, make_key

pytestmark = pytest.mark.medium


@contextlib.contextmanager
def _no_lock(_path, _timeout):
    """Stand in for the file lock."""
    yield


@pytest.fixture
def parts(tmp_path):
    """Return the store and the publisher over one packages root."""
    root = tmp_path / "packages"
    publisher = LinkPublisher(PackageLocks(root, factory=_no_lock), StableLink(root, windows=True))
    return PackageStore(root), publisher


def test_publish_points_the_link_at_the_package(parts):
    """Check that the published link reaches the package's config folder."""
    store, publisher = parts
    package = install(store, make_key())
    link = publisher.publish(package, "c1", "sushiai")
    assert (link / "prefix" / "lib" / "cmake" / "SushiRuntime").is_dir()


def test_links_of_two_consumers_protect_two_digests(parts):
    """Check that the digests two consumers' links name are protected, and one link moves."""
    store, publisher = parts
    first = install(store, make_key(source="s1"))
    second = install(store, make_key(source="s2"))
    publisher.publish(first, "c1", "sushiai")
    publisher.publish(first, "c1", "sushiengine")
    publisher.publish(second, "c1", "sushiai")
    assert publisher.protected("sushiruntime") == {first.digest, second.digest}
