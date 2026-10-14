# test_rocm_selection.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""The newest release with one family covering every card is chosen, the leanest family first."""

from __future__ import annotations

from sushicore.provision.gpu.amd_hardware import AmdHardware
from sushicore.provision.gpu.rocm_package import RocmPackage
from sushicore.provision.gpu.rocm_selection import select_package


def _p(version: tuple[int, ...], family: str) -> RocmPackage:
    """Return a tarball of *family* at *version*."""
    return RocmPackage(version, family, f"https://example.invalid/{family}")


K_PACKAGES = [
    _p((7, 13, 0), "gfx103X-all"), _p((7, 13, 0), "gfx110X-all"),
    _p((7, 10, 0), "gfx110X-dgpu"), _p((7, 13, 0), "gfx1151"), _p((7, 12, 0), "gfx1151"),
    _p((7, 13, 0), "gfx115X-all"),
]


def test_the_newest_release_of_the_covering_family_is_chosen():
    """Check that an RDNA3 iGPU gets 7.13.0 gfx110X-all."""
    chosen = select_package(AmdHardware(("gfx1103",)), K_PACKAGES)

    assert chosen.label == "7.13.0-gfx110X-all"


def test_an_exact_family_beats_a_wildcard_one():
    """Check that gfx1151 is preferred to gfx115X-all for the same release."""
    assert select_package(AmdHardware(("gfx1151",)), K_PACKAGES).family == "gfx1151"


def test_cards_no_single_family_covers_get_nothing():
    """Check that an RDNA2 and an RDNA3 card together find no one tarball."""
    assert select_package(AmdHardware(("gfx1030", "gfx1100")), K_PACKAGES) is None


def test_two_cards_of_one_family_share_its_tarball():
    """Check that two RDNA3 cards get the family that covers both."""
    chosen = select_package(AmdHardware(("gfx1100", "gfx1103")), K_PACKAGES)

    assert chosen.label == "7.13.0-gfx110X-all"
