# test_base_fragment.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the shared base fragment."""

from __future__ import annotations

import pytest

from sushicore import deps_fragment
from sushicore.provision import manifests


pytestmark = pytest.mark.medium


def test_the_base_fragment_declares_the_base_tools():
    """The shared base fragment on disk declares the tools every module builds with."""
    names = {dep.name for dep in deps_fragment.read(manifests.base_fragment()).dependencies}
    assert {"cmake", "ninja", "gtest", "opencl", "pkgconf", "build_tools"} <= names


def test_base_fragment_declares_no_module_dependency():
    """The shared base fragment on disk depends on no module."""
    assert deps_fragment.read(manifests.base_fragment()).depends_on == []



def test_the_base_fragment_pins_cmake_and_git_for_windows():
    """Check that the shipped fragment pins a whole download for each tool it names."""
    entries = {dep.name: dep for dep in deps_fragment.read(manifests.base_fragment()).dependencies}
    for name in ("cmake", "git"):
        pinned = entries[name].download_for("windows")
        assert pinned is not None and pinned.version and pinned.url.startswith("https://")


def test_the_base_fragment_pins_each_clone_and_the_oneapi_key():
    """Check that vcpkg, AdaptiveCpp and Unified Runtime pin a full commit and the key a fingerprint."""
    entries = {dep.name: dep for dep in deps_fragment.read(manifests.base_fragment()).dependencies}
    for name in ("vcpkg", "adaptivecpp", "unified-runtime"):
        pin = entries[name].git_pin()
        assert pin is not None and pin.ref and len(pin.commit) == 40
    key = entries["oneapi-apt-key"].key_pin()
    assert key is not None and len(key.fingerprint) == 40
