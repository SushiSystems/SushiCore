# test_linux.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests the Linux package managers and the names the packages package exports for hub."""

from __future__ import annotations

import subprocess

import pytest

from sushicore.provision import packages
from sushicore.provision.packages import linux


pytestmark = pytest.mark.small


def test_every_manager_is_exported():
    """Check that every manager is exported."""
    for name in ("IPackageManager", "AptManager", "DnfManager", "YumManager",
                 "PacmanManager", "ZypperManager", "WingetManager",
                 "DirectDownloadWindowsManager", "VcpkgManager"):
        assert hasattr(packages, name), name


def test_the_exported_names_are_public_and_resolve():
    """Check that the exported names are public and resolve."""
    assert [name for name in packages.__all__ if name.startswith("_")] == []
    for name in packages.__all__:
        assert hasattr(packages, name), name


def test_the_shared_helpers_are_exported_under_public_names():
    """Check that the shared helpers are exported under public names."""
    for name in ("download", "gh_latest_asset", "gh_latest_asset_including_prerelease",
                 "gh_latest_release_asset", "gh_tagged_asset", "run", "tools_dir"):
        assert name in packages.__all__, name


def test_dnf_translates_apt_names_and_keeps_unknown_ones():
    assert linux.DnfManager().translate_apt(["build-essential", "cmake", "ocl-icd-libopencl1"]) == [
        "gcc", "gcc-c++", "make", "cmake",
    ]


def test_apt_keeps_its_own_names():
    assert linux.AptManager().translate_apt(["pkg-config"]) == ["pkg-config"]


def test_apt_is_installed_reads_the_dpkg_status(monkeypatch):
    status = subprocess.CompletedProcess([], 0, "install ok installed", "")
    monkeypatch.setattr(linux.subprocess, "run", lambda *args, **kwargs: status)
    assert linux.AptManager().is_installed("cmake")


def test_apt_install_updates_then_installs_without_sudo_as_root(monkeypatch):
    calls = []
    monkeypatch.setattr(linux, "is_root", lambda: True)
    monkeypatch.setattr(linux, "run", lambda command, dry_run, check=False: calls.append(command) or 0)
    assert linux.AptManager().install(["cmake"], dry_run=False)
    assert calls == [["apt-get", "update"], ["apt-get", "install", "-y", "cmake"]]


def test_apt_install_of_nothing_runs_nothing(monkeypatch):
    monkeypatch.setattr(linux, "run", lambda *args, **kwargs: pytest.fail("ran a command"))
    assert linux.AptManager().install([], dry_run=False)
