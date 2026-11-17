# test_linux.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the package exports and the Linux package managers."""

from __future__ import annotations

import os
import subprocess

import pytest

from sushicore.provision import packages
from sushicore.provision.packages import base, linux
from sushicore.provision.packages.base_memory import InMemoryLinuxPackageManager


class _Process:
    """Stands in for the process Popen starts: no output, a scripted exit code."""

    def __init__(self, returncode: int = 0) -> None:
        """Store the exit code the process ends with."""
        self.stdout = None
        self.returncode = returncode

    def wait(self) -> None:
        """Do nothing, since nothing runs."""


def _started(monkeypatch, returncode: int = 0) -> list[list[str]]:
    """Replace the process start at the boundary; return the commands it was asked to start."""
    commands: list[list[str]] = []

    def popen(command, **_options):
        """Record the command and answer a finished process."""
        commands.append(list(command))
        return _Process(returncode)

    monkeypatch.setattr(base.subprocess, "Popen", popen)
    return commands


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
    "WingetManager", "DirectDownloadWindowsManager", "VcpkgManager", "download", "gh_latest_asset",
    "tools_dir"])
def test_an_exported_name_resolves(name):
    """Check that a name the package lists is a name it holds."""
    assert name in packages.__all__ and hasattr(packages, name)


@pytest.mark.small
@pytest.mark.parametrize("name", [
    "download", "gh_latest_asset", "gh_latest_asset_including_prerelease",
    "gh_latest_release_asset", "gh_tagged_asset", "tools_dir"])
def test_the_shared_helpers_are_exported_under_public_names(name):
    """Check that a helper the hub uses is exported."""
    assert name in packages.__all__


@pytest.mark.small
@pytest.mark.parametrize(("apt_names", "native"), [
    (["build-essential"], ["gcc", "gcc-c++", "make"]),
    (["ocl-icd-libopencl1"], []),
    (["cmake"], ["cmake"]),
], ids=["a mapped name", "a name with no native package", "an unknown name is kept"])
def test_dnf_translates_apt_names(apt_names, native):
    """Check how dnf maps an apt name: to its packages, to none, or to itself."""
    assert linux.DnfManager().translate_apt(apt_names) == native


@pytest.mark.small
def test_apt_keeps_its_own_names():
    """Check that apt names are apt's own."""
    assert linux.AptManager().translate_apt(["pkg-config"]) == ["pkg-config"]


@pytest.mark.small
def test_apt_is_installed_reads_the_dpkg_status(monkeypatch):
    """Check that a dpkg status of installed reads as installed."""
    status = subprocess.CompletedProcess([], 0, "install ok installed", "")
    monkeypatch.setattr(linux.subprocess, "run", lambda *args, **kwargs: status)
    assert linux.AptManager().is_installed("cmake")


@pytest.mark.small
def test_apt_install_updates_then_installs_without_sudo_as_root(monkeypatch, recording_console):
    """Check that as root apt updates its cache and then installs, with no sudo."""
    monkeypatch.setattr(os, "geteuid", lambda: 0, raising=False)
    commands = _started(monkeypatch)
    assert linux.AptManager().install(["cmake"], dry_run=False)
    assert commands == [["apt-get", "update"], ["apt-get", "install", "-y", "cmake"]]


@pytest.mark.small
def test_apt_install_of_nothing_runs_nothing(monkeypatch, recording_console):
    """Check that an empty list starts no process and succeeds."""
    commands = _started(monkeypatch)
    assert linux.AptManager().install([], dry_run=False)
    assert commands == []


_MANAGERS = [
    pytest.param(linux.AptManager, id="apt"),
    pytest.param(linux.DnfManager, id="dnf"),
    pytest.param(linux.YumManager, id="yum"),
    pytest.param(linux.PacmanManager, id="pacman"),
    pytest.param(linux.ZypperManager, id="zypper"),
    pytest.param(InMemoryLinuxPackageManager, id="in-memory"),
]


@pytest.fixture(params=_MANAGERS)
def manager(request) -> linux.LinuxPackageManager:
    """Give each Linux manager the contract is held against, one at a time."""
    return request.param()


@pytest.mark.small
def test_a_manager_is_named(manager):
    """Check that every manager carries a non-empty name."""
    assert isinstance(manager.name, str) and manager.name


@pytest.mark.small
def test_translating_nothing_gives_nothing(manager):
    """Check that translating no names gives no names."""
    assert list(manager.translate_apt([])) == []


@pytest.mark.small
def test_a_name_no_table_knows_passes_through_unchanged(manager):
    """Check that a name outside every table comes back as it went in."""
    assert list(manager.translate_apt(["a-package-no-table-lists"])) == ["a-package-no-table-lists"]


@pytest.mark.small
def test_translation_keeps_the_order_of_the_names_it_keeps(manager):
    """Check that names no table lists keep the order they were given in."""
    names = ["zz-unlisted", "aa-unlisted"]
    assert list(manager.translate_apt(names)) == names


@pytest.mark.small
def test_translation_leaves_the_names_it_was_given_untouched(manager):
    """Check that translating does not change the list it was handed."""
    names = ["build-essential", "pkg-config"]
    manager.translate_apt(names)
    assert names == ["build-essential", "pkg-config"]
