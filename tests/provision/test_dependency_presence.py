# test_dependency_presence.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""How a manifest dependency is found installed, and which manager answers for it."""

from __future__ import annotations

import pytest

from sushicore.provision.dependency_presence import (
    available_linux_manager,
    dep_installed,
    dep_manager,
    held_by_managers,
    manager_holds,
    named_manager,
    vcpkg_manager,
)
from sushicore.provision.fragments import Dependency
from sushicore.provision.packages.base_memory import InMemoryPackageManager


pytestmark = pytest.mark.small


def _apt_dep() -> Dependency:
    """Build a dependency that apt supplies as one package."""
    return Dependency(name="zlib", linux_apt=["zlib1g-dev"])


def _vcpkg_only_dep() -> Dependency:
    """Build a dependency that only vcpkg supplies, on every platform."""
    return Dependency(name="fmt", windows_vcpkg=["fmt"])


def test_manager_holds_is_true_when_the_manager_has_every_package_of_the_dependency():
    """Check that a dependency is held when its manager reports all its packages installed."""
    apt = InMemoryPackageManager("apt", installed=["zlib1g-dev"])

    assert manager_holds(_apt_dep(), apt, "linux")


def test_manager_holds_is_false_when_the_manager_lacks_a_package():
    """Check that a dependency is not held when its manager misses its package."""
    assert not manager_holds(_apt_dep(), InMemoryPackageManager("apt"), "linux")


def test_manager_holds_is_false_without_a_manager():
    """Check that a dependency with packages is not held when no manager answers for it."""
    assert not manager_holds(_apt_dep(), None, "linux")


def test_manager_holds_asks_vcpkg_for_a_dependency_with_no_apt_package_on_linux():
    """Check that the vcpkg fallback ports are asked of vcpkg, not of the Linux manager."""
    vcpkg = InMemoryPackageManager("vcpkg", installed=["fmt"])

    assert manager_holds(_vcpkg_only_dep(), InMemoryPackageManager("apt"), "linux", vcpkg)


def test_manager_holds_is_false_for_a_dependency_with_no_package_at_all():
    """Check that a dependency that names no package is never held."""
    assert not manager_holds(Dependency(name="nothing"), InMemoryPackageManager("apt"), "linux")


def test_dep_installed_falls_back_to_the_manager_when_there_is_no_check_command():
    """Check that a dependency without a check command is found through its manager."""
    apt = InMemoryPackageManager("apt", installed=["zlib1g-dev"])

    assert dep_installed(_apt_dep(), apt, "linux")


def test_named_manager_returns_the_manager_of_that_name():
    """Check that the manager with the asked name is the one returned."""
    winget = InMemoryPackageManager("winget")

    assert named_manager([InMemoryPackageManager("vcpkg"), winget], "winget") is winget


def test_named_manager_is_none_when_no_manager_has_that_name():
    """Check that an absent manager name answers None."""
    assert named_manager([InMemoryPackageManager("vcpkg")], "winget") is None


def test_vcpkg_manager_returns_the_vcpkg_manager():
    """Check that the manager named vcpkg is the one returned."""
    vcpkg = InMemoryPackageManager("vcpkg")

    assert vcpkg_manager([InMemoryPackageManager("apt"), vcpkg]) is vcpkg


def test_available_linux_manager_takes_the_first_of_the_list_order_that_is_available():
    """Check that an unavailable apt is skipped and dnf, next in the list, is chosen."""
    dnf = InMemoryPackageManager("dnf")
    managers = [InMemoryPackageManager("zypper"), dnf, InMemoryPackageManager("apt", is_available=False)]

    assert available_linux_manager(managers) is dnf


def test_available_linux_manager_ignores_a_manager_that_is_not_a_linux_one():
    """Check that vcpkg is never chosen as the Linux manager."""
    assert available_linux_manager([InMemoryPackageManager("vcpkg")]) is None


def test_dep_manager_is_vcpkg_on_windows_and_a_linux_manager_elsewhere():
    """Check that Windows answers through vcpkg and Linux through its available system manager."""
    vcpkg, apt = InMemoryPackageManager("vcpkg"), InMemoryPackageManager("apt")

    assert (dep_manager([apt, vcpkg], "windows"), dep_manager([apt, vcpkg], "linux")) == (vcpkg, apt)


def test_detect_and_install_pick_the_same_manager_when_two_are_available_in_reverse_order():
    """Check that dep_manager (detect) and available_linux_manager (install) both take apt over dnf."""
    apt, dnf = InMemoryPackageManager("apt"), InMemoryPackageManager("dnf")
    managers = [dnf, apt]

    assert (dep_manager(managers, "linux"), available_linux_manager(managers)) == (apt, apt)


def test_held_by_managers_asks_the_manager_first_in_the_linux_order():
    """Check that detect reads the apt manager, not the dnf listed before it."""
    apt = InMemoryPackageManager("apt", installed=["zlib1g-dev"])
    held = held_by_managers([InMemoryPackageManager("dnf"), apt], "linux")

    assert held(_apt_dep())


def test_held_by_managers_tells_whether_the_wired_managers_hold_a_dependency():
    """Check that the predicate answers True for a held dependency and False for a missing one."""
    held = held_by_managers([InMemoryPackageManager("apt", installed=["zlib1g-dev"])], "linux")

    assert (held(_apt_dep()), held(Dependency(name="curl", linux_apt=["libcurl4-openssl-dev"]))) == (True, False)
