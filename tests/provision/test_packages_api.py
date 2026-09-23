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
