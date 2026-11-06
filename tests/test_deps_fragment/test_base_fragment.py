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

