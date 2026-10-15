# test_rocm_tarball_index.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""AMD's listing is read for each platform's tarballs, newest first."""

from __future__ import annotations

import pytest

from sushicore.provision.gpu.rocm_package import RocmPackage
from sushicore.provision.gpu.rocm_tarball_index import RocmIndexError, RocmTarballIndex


pytestmark = pytest.mark.small

K_ROOT = "https://example.invalid/tarball/"
K_LISTING = (
    'const files = [{"name": "therock-dist-linux-gfx110X-all-7.12.0.tar.gz"}, '
    '{"name": "therock-dist-linux-gfx110X-all-7.13.0.tar.gz"}, '
    '{"name": "therock-dist-linux-gfx1151-7.13.0.tar.gz"}, '
    '{"name": "therock-dist-windows-gfx110X-all-7.13.0.tar.gz"}]; '
    '<a href="therock-dist-linux-gfx1151-7.13.0.tar.gz">x</a>'
)


def test_packages_lists_one_platform_newest_first_without_duplicates():
    """Check the filter, the order and that a name met twice counts once."""
    packages = RocmTarballIndex(lambda url: K_LISTING, K_ROOT).packages("linux")

    assert packages == [
        RocmPackage((7, 13, 0), "gfx1151", f"{K_ROOT}therock-dist-linux-gfx1151-7.13.0.tar.gz"),
        RocmPackage((7, 13, 0), "gfx110X-all",
                    f"{K_ROOT}therock-dist-linux-gfx110X-all-7.13.0.tar.gz"),
        RocmPackage((7, 12, 0), "gfx110X-all",
                    f"{K_ROOT}therock-dist-linux-gfx110X-all-7.12.0.tar.gz"),
    ]


def test_an_unreachable_listing_raises():
    """Check that a transport failure is a RocmIndexError."""
    def fail(url):
        """Fail as an unreachable host does."""
        raise OSError("no route")

    with pytest.raises(RocmIndexError):
        RocmTarballIndex(fail, K_ROOT).packages("linux")
