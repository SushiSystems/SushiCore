# test_rocm_vendor_memory.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""What the in-memory tarball index and installer promise as stand-ins for their ports."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.provision.gpu.rocm_package import RocmPackage
from sushicore.provision.gpu.rocm_vendor_memory import (
    InMemoryTarballIndex,
    InMemoryTarballInstaller,
)

pytestmark = pytest.mark.small

K_PACKAGES = [RocmPackage((7, 13, 0), "gfx110X-all", "https://example.invalid/a"),
              RocmPackage((7, 12, 0), "gfx110X-all", "https://example.invalid/b")]


@pytest.mark.parametrize("platform", ["linux", "windows"])
def test_the_index_lists_the_same_tarballs_for_every_platform(platform):
    """Check that the platform does not change the listing."""
    assert InMemoryTarballIndex(K_PACKAGES).packages(platform) == K_PACKAGES


def test_the_index_hands_out_a_copy_of_its_list():
    """Check that clearing a returned list does not empty the index."""
    index = InMemoryTarballIndex(K_PACKAGES)

    index.packages("linux").clear()

    assert index.packages("linux") == K_PACKAGES


def test_the_installer_records_each_tarball_and_returns_its_label_as_a_path():
    """Check that an install records the tarball and returns a path named by its label."""
    installer = InMemoryTarballInstaller()

    root = installer.install(K_PACKAGES[0])

    assert installer.installed == [K_PACKAGES[0]]
    assert root == Path("7.13.0-gfx110X-all")
