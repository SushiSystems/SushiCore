# test_linux.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the package exports and the Linux package managers."""

from __future__ import annotations

import os

import pytest

from sushicore.proc_memory import RecordingRunner
from sushicore.provision import packages
from sushicore.provision.packages import linux
from sushicore.provision.packages.base_memory import InMemoryLinuxPackageManager


@pytest.fixture
def runner(recording_console) -> RecordingRunner:
    """Build the runner that records the commands of a manager and starts none."""
    return RecordingRunner(recording_console)


def _argv(runner: RecordingRunner) -> list[list[str]]:
    """Return the commands *runner* was asked to run, as lists."""
    return [list(command.argv) for command in runner.commands]


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


@pytest.mark.small
@pytest.mark.parametrize(("apt_names", "native"), [
    (["build-essential"], ["gcc", "gcc-c++", "make"]),
    (["ocl-icd-libopencl1"], []),
    (["cmake"], ["cmake"]),
], ids=["a mapped name", "a name with no native package", "an unknown name is kept"])
def test_dnf_translates_apt_names(apt_names, native, recording_console):
    """Check how dnf maps an apt name: to its packages, to none, or to itself."""
    assert linux.DnfManager(console=recording_console).translate_apt(apt_names) == native


@pytest.mark.small
def test_apt_keeps_its_own_names(recording_console):
    """Check that apt names are apt's own."""
    apt = linux.AptManager(console=recording_console)
    assert apt.translate_apt(["pkg-config"]) == ["pkg-config"]


@pytest.mark.small
def test_apt_is_installed_reads_the_dpkg_status(runner, recording_console):
    """Check that a dpkg status of installed reads as installed."""
    runner.script(0, ("install ok installed",))
    assert linux.AptManager(runner, console=recording_console).is_installed("cmake")


@pytest.mark.small
def test_apt_install_updates_then_installs_without_sudo_as_root(
        monkeypatch, runner, recording_console):
    """Check that as root apt updates its cache and then installs, with no sudo."""
    monkeypatch.setattr(os, "geteuid", lambda: 0, raising=False)
    assert linux.AptManager(runner, console=recording_console).install(["cmake"], dry_run=False)
    assert _argv(runner) == [["apt-get", "update"], ["apt-get", "install", "-y", "cmake"]]


@pytest.mark.small
def test_apt_install_of_nothing_runs_nothing(runner, recording_console):
    """Check that an empty list starts no process and succeeds."""
    assert linux.AptManager(runner, console=recording_console).install([], dry_run=False)
    assert _argv(runner) == []


_MANAGERS = [
    pytest.param(lambda console: linux.AptManager(console=console), id="apt"),
    pytest.param(lambda console: linux.DnfManager(console=console), id="dnf"),
    pytest.param(lambda console: linux.YumManager(console=console), id="yum"),
    pytest.param(lambda console: linux.PacmanManager(console=console), id="pacman"),
    pytest.param(lambda console: linux.ZypperManager(console=console), id="zypper"),
    pytest.param(lambda console: InMemoryLinuxPackageManager(), id="in-memory"),
]


@pytest.fixture(params=_MANAGERS)
def manager(request, recording_console) -> linux.LinuxPackageManager:
    """Give each Linux manager the contract is held against, one at a time."""
    return request.param(recording_console)


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


@pytest.mark.small
@pytest.mark.parametrize(("manager", "gpu", "oneapi"), [
    (linux.AptManager, True, True), (linux.DnfManager, False, False),
    (linux.YumManager, False, False), (linux.PacmanManager, False, False),
    (linux.ZypperManager, False, False),
])
def test_only_apt_automates_the_gpu_sdk_and_oneapi(manager, gpu, oneapi, recording_console):
    """Check that the manager says whether it installs the GPU SDK and oneAPI."""
    assert (manager(console=recording_console).automates_gpu_sdk,
            manager(console=recording_console).automates_oneapi) == (gpu, oneapi)


@pytest.mark.small
def test_a_manager_without_oneapi_automation_installs_nothing_for_it(recording_console):
    """Check that install_oneapi of a manager that does not automate it reports failure."""
    assert linux.DnfManager(console=recording_console).install_oneapi(True) is False
