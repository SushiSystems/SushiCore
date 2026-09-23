# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Pins the package-manager names hub imports."""

from __future__ import annotations

from sushicore.provision import packages


def test_every_manager_is_exported():
    for name in ("IPackageManager", "AptManager", "DnfManager", "YumManager",
                 "PacmanManager", "ZypperManager", "WingetManager",
                 "DirectDownloadWindowsManager", "VcpkgManager"):
        assert hasattr(packages, name), name


def test_the_exported_names_are_public_and_resolve():
    assert [name for name in packages.__all__ if name.startswith("_")] == []
    for name in packages.__all__:
        assert hasattr(packages, name), name


def test_the_shared_helpers_are_exported_under_public_names():
    for name in ("download", "gh_latest_asset", "gh_latest_asset_including_prerelease",
                 "gh_latest_release_asset", "gh_tagged_asset", "run", "tools_dir"):
        assert name in packages.__all__, name
