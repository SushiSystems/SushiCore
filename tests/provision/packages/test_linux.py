# test_linux.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the deprecated module that re-exports the Linux package managers."""

from __future__ import annotations

import importlib
import sys

import pytest

from sushicore.provision.packages import (
    AptManager,
    DnfManager,
    LinuxPackageManager,
    PacmanManager,
    YumManager,
    ZypperManager,
)

pytestmark = pytest.mark.small

_NAME = "sushicore.provision.packages.linux"


def _import_fresh():
    """Import the module as its first importer does."""
    sys.modules.pop(_NAME, None)
    return importlib.import_module(_NAME)


def test_the_module_re_exports_each_manager_it_held():
    """Check that every old name is the object the new module holds."""
    with pytest.warns(DeprecationWarning):
        old = _import_fresh()
    assert (old.LinuxPackageManager, old.AptManager, old.DnfManager,
            old.YumManager, old.PacmanManager, old.ZypperManager) == (
        LinuxPackageManager, AptManager, DnfManager, YumManager, PacmanManager, ZypperManager)


def test_importing_the_module_warns_with_the_replacement():
    """Check that the message names the module it is deprecated for."""
    with pytest.warns(DeprecationWarning, match="apt_manager"):
        _import_fresh()
