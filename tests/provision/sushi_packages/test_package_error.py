# test_package_error.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests for the shape of the package errors."""

from __future__ import annotations

import pytest

from sushicore.errors import SushiCoreError
from sushicore.provision.sushi_packages.package_error import PackageConflictError, PackageError

pytestmark = pytest.mark.small


def test_a_package_error_is_a_sushicore_error():
    """Check that the entry point catches a package error as a SushiCore one."""
    assert issubclass(PackageError, SushiCoreError)


def test_a_conflict_is_a_package_error():
    """Check that a conflict is caught wherever a package error is."""
    assert issubclass(PackageConflictError, PackageError)
