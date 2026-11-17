# test_apt_names.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the apt-name translation the non-apt managers share."""

from __future__ import annotations

import pytest

from sushicore.provision.packages.apt_names import K_APT_TO_DNF, K_APT_TO_PACMAN, translate_names


@pytest.mark.small
@pytest.mark.parametrize(("names", "native"), [
    (["build-essential"], ["gcc", "gcc-c++", "make"]),
    (["ocl-icd-libopencl1"], []),
    (["cmake"], ["cmake"]),
    (["pkg-config", "cmake"], ["pkgconf", "cmake"]),
], ids=["a mapped name", "a name with no native package", "an unknown name is kept",
        "order is kept"])
def test_translate_names_maps_through_the_table(names, native):
    """Check how a name maps: to its packages, to none, or to itself."""
    assert translate_names(names, K_APT_TO_DNF) == native


@pytest.mark.small
def test_each_table_names_its_own_build_group():
    """Check that pacman's build group differs from the dnf one."""
    assert translate_names(["build-essential"], K_APT_TO_PACMAN) == ["base-devel"]
