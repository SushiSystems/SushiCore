# test_link_publisher.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the publication of a consumer link."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.provision.sushi_packages.link_publisher import LinkPublisher
from sushicore.provision.sushi_packages.package import Package
from sushicore.provision.sushi_packages.package_error import PackageError
from sushicore.provision.sushi_packages.package_locks import MemoryLocks, PackageLocks
from sushicore.provision.sushi_packages.package_store import PackageStore
from sushicore.provision.sushi_packages.stable_link import MemoryLinks, StableLink

from .package_fakes import install, make_key


@pytest.mark.medium
def test_publish_points_the_link_at_the_package(tmp_path):
    """Check that the published link reaches the package's config folder."""
    root = tmp_path / "packages"
    publisher = LinkPublisher(PackageLocks(root, factory=MemoryLocks()),
                              StableLink(root, windows=True))
    package = install(PackageStore(root), make_key())
    link = publisher.publish(package, "c1", "sushiai")
    assert (link / "prefix" / "lib" / "cmake" / "SushiRuntime").is_dir()


@pytest.mark.small
def test_publish_raises_naming_the_package_when_the_link_cannot_be_made():
    """Check that a link store that fails reaches the caller as a package error."""
    publisher = LinkPublisher(PackageLocks(Path("packages"), factory=MemoryLocks()),
                              MemoryLinks(error=OSError("access denied")))
    package = Package("sushiruntime", "d" * 64, Path("packages/sushiruntime/d"), {})
    with pytest.raises(PackageError, match="sushiruntime"):
        publisher.publish(package, "c1", "sushiai")
