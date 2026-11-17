# test_base.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the package-manager contract and the names the packages module exports."""

from __future__ import annotations

import pytest

from sushicore.provision import packages
from sushicore.provision.packages.base import IPackageManager


class _Minimal(IPackageManager):
    """A manager that implements only what the contract requires."""

    name = "minimal"

    def available(self) -> bool:
        """Report that the tool is present."""
        return True

    def is_installed(self, pkg: str) -> bool:
        """Report that nothing is installed."""
        return False

    def install(self, pkgs: list[str], dry_run: bool) -> bool:
        """Report success without installing."""
        return True


@pytest.mark.small
def test_remove_defaults_to_a_warning_and_success(recording_console):
    """Check that a manager with no remove warns, names itself and reports success."""
    manager = _Minimal(console=recording_console)
    assert manager.remove(["pkg"], dry_run=False) is True
    assert recording_console.calls == [("warn", ("minimal: remove not implemented, skipping.",))]


@pytest.mark.small
@pytest.mark.parametrize("name", [
    "IPackageManager", "AptManager", "DnfManager", "YumManager", "PacmanManager", "ZypperManager",
    "WingetManager", "DirectDownloadWindowsManager", "VcpkgManager"])
def test_every_manager_is_exported(name):
    """Check that the package exports the manager."""
    assert hasattr(packages, name)


@pytest.mark.small
def test_no_exported_name_is_private():
    """Check that no exported name starts with an underscore."""
    assert [name for name in packages.__all__ if name.startswith("_")] == []


@pytest.mark.small
@pytest.mark.parametrize("name", [
    "IPackageManager", "AptManager", "DnfManager", "YumManager", "PacmanManager", "ZypperManager",
    "WingetManager", "DirectDownloadWindowsManager", "VcpkgManager", "download", "gh_tagged_asset",
    "tools_dir"])
def test_an_exported_name_resolves(name):
    """Check that a name the package lists is a name it holds."""
    assert name in packages.__all__ and hasattr(packages, name)


@pytest.mark.small
@pytest.mark.parametrize("name", [
    "download", "gh_tagged_asset", "tools_dir"])
def test_the_shared_helpers_are_exported_under_public_names(name):
    """Check that a helper the hub uses is exported."""
    assert name in packages.__all__
