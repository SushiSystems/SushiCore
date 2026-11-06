# test_rocm_vendor.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""AMD's answers: the family that covers the cards, the override, and the install."""

from __future__ import annotations

import pytest

from sushicore.provision.gpu.amd_hardware import AmdHardware
from sushicore.provision.gpu.rocm_package import RocmPackage
from sushicore.provision.gpu.rocm_tarball_index import RocmIndexError
from sushicore.provision.gpu.rocm_vendor import RocmVendor
from sushicore.provision.gpu.rocm_vendor_memory import (
    InMemoryTarballIndex,
    InMemoryTarballInstaller,
)

pytestmark = pytest.mark.small


def _p(version: tuple[int, ...], family: str) -> RocmPackage:
    """Return a tarball of *family* at *version*."""
    return RocmPackage(version, family, f"https://example.invalid/{family}")


K_PACKAGES = [_p((7, 13, 0), "gfx110X-all"), _p((7, 13, 0), "gfx103X-all"),
              _p((7, 12, 0), "gfx110X-all")]


@pytest.fixture
def parts():
    """Return a ROCm vendor for one RDNA3 card, and the installer it installs through."""
    installer = InMemoryTarballInstaller()
    vendor = RocmVendor(lambda: AmdHardware(("gfx1103",)), InMemoryTarballIndex(K_PACKAGES),
                        installer)
    return vendor, installer


def test_an_override_release_keeps_the_family_the_cards_need(parts):
    """Check that ``7.12`` picks 7.12.0 of the RDNA3 family."""
    vendor, _installer = parts

    assert vendor.resolve_override("7.12") == "7.12.0-gfx110X-all"


def test_an_override_with_a_family_names_it_exactly(parts):
    """Check that a full label is taken as written."""
    vendor, _installer = parts

    assert vendor.resolve_override("7.13.0-gfx103X-all") == "7.13.0-gfx103X-all"


def test_an_override_that_is_not_a_release_raises(parts):
    """Check that a word is refused with the vendor's own error."""
    vendor, _installer = parts

    with pytest.raises(RocmIndexError):
        vendor.resolve_override("latest")


def test_install_hands_the_listed_tarball_to_the_installer(parts):
    """Check that a label becomes the right tarball."""
    vendor, installer = parts

    vendor.install("7.12.0-gfx110X-all")

    assert installer.installed == [_p((7, 12, 0), "gfx110X-all")]


def test_a_label_no_longer_listed_raises(parts):
    """Check that a release AMD withdrew is reported."""
    vendor, _installer = parts

    with pytest.raises(RocmIndexError):
        vendor.install("6.0.0-gfx110X-all")
