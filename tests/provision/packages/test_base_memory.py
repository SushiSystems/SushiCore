# test_base_memory.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""What the in-memory Linux package manager promises: it holds packages and runs no command."""

from __future__ import annotations

import pytest

from sushicore.provision.packages.base_memory import InMemoryLinuxPackageManager


@pytest.mark.small
def test_an_install_holds_the_packages_and_is_recorded():
    manager = InMemoryLinuxPackageManager()
    assert manager.install(["a", "b"], False) is True
    assert (manager.is_installed("a"), manager.installs) == (True, [["a", "b"]])


@pytest.mark.small
def test_a_dry_run_install_is_recorded_and_holds_nothing():
    manager = InMemoryLinuxPackageManager()
    manager.install(["a"], True)
    assert (manager.is_installed("a"), manager.installs) == (False, [["a"]])


@pytest.mark.small
def test_a_removal_drops_the_packages_and_is_recorded():
    manager = InMemoryLinuxPackageManager(installed=["a", "b"])
    manager.remove(["a"], False)
    assert (manager.held, manager.removals) == ({"b"}, [["a"]])


@pytest.mark.small
def test_a_failing_manager_reports_failure_and_holds_nothing():
    manager = InMemoryLinuxPackageManager(succeeds=False)
    assert (manager.install(["a"], False), manager.is_installed("a")) == (False, False)


@pytest.mark.small
def test_an_absent_manager_reports_itself_absent():
    assert InMemoryLinuxPackageManager(is_available=False).available() is False
