# test_rocm_package.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""A tarball's family name says which cards it covers."""

from __future__ import annotations

import pytest

from sushicore.provision.gpu.rocm_package import RocmPackage


pytestmark = pytest.mark.small


def _package(family: str) -> RocmPackage:
    """Return a 7.13.0 tarball of *family*."""
    return RocmPackage((7, 13, 0), family, f"https://example.invalid/{family}.tar.gz")


@pytest.mark.parametrize(("family", "target", "covered"), [
    ("gfx110X-all", "gfx1103", True),
    ("gfx110X-all", "gfx1030", False),
    ("gfx1151", "gfx1151", True),
    ("gfx1151", "gfx1150", False),
    ("gfx90X-dcgpu", "gfx90a", True),
    ("gfx90X-dcgpu", "gfx1100", False),
])
def test_builds_for_reads_x_as_any_character(family, target, covered):
    """Check the wildcard and the length rule."""
    assert _package(family).builds_for(target) is covered


def test_label_joins_release_and_family():
    """Check the install folder's name."""
    assert _package("gfx110X-all").label == "7.13.0-gfx110X-all"


def test_an_exact_family_is_more_specific_than_a_wildcard_one():
    """Check that gfx1151 ranks above gfx115X."""
    assert _package("gfx1151").specificity() > _package("gfx115X-all").specificity()
