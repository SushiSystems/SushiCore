# test_rocm_vendor.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""AMD's answers: the family that covers the cards, the override, and the install."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.provision.gpu.amd_hardware import AmdHardware
from sushicore.provision.gpu.rocm_package import RocmPackage
from sushicore.provision.gpu.rocm_tarball_index import RocmIndexError
from sushicore.provision.gpu.rocm_vendor import RocmVendor
from sushicore.provision.gpu.toolkit_vendor import ToolkitVendor


def _p(version: tuple[int, ...], family: str) -> RocmPackage:
    """Return a tarball of *family* at *version*."""
    return RocmPackage(version, family, f"https://example.invalid/{family}")


class _Index:
    """Lists fixed Linux tarballs."""

    def packages(self, platform):
        """Return the tarballs, newest first."""
        assert platform == "linux"
        return [_p((7, 13, 0), "gfx110X-all"), _p((7, 13, 0), "gfx103X-all"),
                _p((7, 12, 0), "gfx110X-all")]


class _Installer:
    """Records the tarballs installed."""

    def __init__(self) -> None:
        """Start with nothing installed."""
        self.installed: list[RocmPackage] = []

    def install(self, package):
        """Record the install."""
        self.installed.append(package)
        return Path(package.label)


@pytest.fixture
def vendor():
    """Return a ROCm vendor for one RDNA3 card over fakes."""
    installer = _Installer()
    found = RocmVendor(lambda: AmdHardware(("gfx1103",)), _Index(), installer)
    found.fake_installer = installer
    return found


def test_the_vendor_answers_the_contract(vendor):
    """Check that the ROCm vendor satisfies the protocol the locator needs."""
    assert isinstance(vendor, ToolkitVendor)


def test_choose_takes_the_newest_covering_family(vendor):
    """Check the label of the chosen tarball."""
    assert vendor.choose(AmdHardware(("gfx1103",))) == "7.13.0-gfx110X-all"


def test_an_override_release_keeps_the_family_the_cards_need(vendor):
    """Check that ``7.12`` picks 7.12.0 of the RDNA3 family."""
    assert vendor.resolve_override("7.12") == "7.12.0-gfx110X-all"


def test_an_override_with_a_family_names_it_exactly(vendor):
    """Check that a full label is taken as written."""
    assert vendor.resolve_override("7.13.0-gfx103X-all") == "7.13.0-gfx103X-all"


def test_an_override_that_is_not_a_release_raises(vendor):
    """Check that a word is refused with the vendor's own error."""
    with pytest.raises(RocmIndexError):
        vendor.resolve_override("latest")


def test_install_hands_the_listed_tarball_to_the_installer(vendor):
    """Check that a label becomes the right tarball."""
    vendor.install("7.12.0-gfx110X-all")

    assert vendor.fake_installer.installed == [_p((7, 12, 0), "gfx110X-all")]


def test_a_label_no_longer_listed_raises(vendor):
    """Check that a release AMD withdrew is reported."""
    with pytest.raises(RocmIndexError):
        vendor.install("6.0.0-gfx110X-all")
