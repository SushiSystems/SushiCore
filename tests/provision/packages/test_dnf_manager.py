# test_dnf_manager.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the dnf package manager."""

from __future__ import annotations

import pytest

from sushicore.provision.packages.dnf_manager import DnfManager


@pytest.mark.small
@pytest.mark.parametrize(("apt_names", "native"), [
    (["build-essential"], ["gcc", "gcc-c++", "make"]),
    (["ocl-icd-libopencl1"], []),
    (["cmake"], ["cmake"]),
], ids=["a mapped name", "a name with no native package", "an unknown name is kept"])
def test_dnf_translates_apt_names(apt_names, native, recording_console):
    """Check how dnf maps an apt name: to its packages, to none, or to itself."""
    assert DnfManager(console=recording_console).translate_apt(apt_names) == native


@pytest.mark.small
def test_a_manager_without_oneapi_automation_installs_nothing_for_it(recording_console):
    """Check that install_oneapi of a manager that does not automate it reports failure."""
    assert DnfManager(console=recording_console).install_oneapi(True) is False
