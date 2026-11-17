# test_linux_manager.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the contract every Linux package manager is held to."""

from __future__ import annotations

import pytest

from sushicore.provision.packages.apt_manager import AptManager
from sushicore.provision.packages.base_memory import InMemoryLinuxPackageManager
from sushicore.provision.packages.dnf_manager import DnfManager
from sushicore.provision.packages.linux_manager import LinuxPackageManager
from sushicore.provision.packages.pacman_manager import PacmanManager
from sushicore.provision.packages.yum_manager import YumManager
from sushicore.provision.packages.zypper_manager import ZypperManager

_MANAGERS = [
    pytest.param(lambda console: AptManager(console=console), id="apt"),
    pytest.param(lambda console: DnfManager(console=console), id="dnf"),
    pytest.param(lambda console: YumManager(console=console), id="yum"),
    pytest.param(lambda console: PacmanManager(console=console), id="pacman"),
    pytest.param(lambda console: ZypperManager(console=console), id="zypper"),
    pytest.param(lambda console: InMemoryLinuxPackageManager(), id="in-memory"),
]


@pytest.fixture(params=_MANAGERS)
def manager(request, recording_console) -> LinuxPackageManager:
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
@pytest.mark.parametrize(("manager_class", "gpu", "oneapi"), [
    (AptManager, True, True), (DnfManager, False, False),
    (YumManager, False, False), (PacmanManager, False, False),
    (ZypperManager, False, False),
])
def test_only_apt_automates_the_gpu_sdk_and_oneapi(manager_class, gpu, oneapi, recording_console):
    """Check that the manager says whether it installs the GPU SDK and oneAPI."""
    built = manager_class(console=recording_console)
    assert (built.automates_gpu_sdk, built.automates_oneapi) == (gpu, oneapi)
