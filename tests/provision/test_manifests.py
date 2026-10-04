# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for the shared base fragment."""

from __future__ import annotations

from sushicore import deps_fragment
from sushicore.provision import fragments, manifests


def test_base_fragment_is_a_readable_file():
    """Check that base fragment is a readable file."""
    names = {dep.name for dep in deps_fragment.read(manifests.base_fragment()).dependencies}
    assert {"cmake", "ninja", "gtest", "opencl", "pkgconf", "build_tools"} <= names


def test_base_fragment_declares_no_module_dependency():
    """Check that base fragment declares no module dependency."""
    assert deps_fragment.read(manifests.base_fragment()).depends_on == []


def test_base_owner_is_the_shared_owner():
    """Check that base owner is the shared owner."""
    assert manifests.BASE_OWNER == fragments.SHARED_OWNER
