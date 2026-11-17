# dependency_presence.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tells whether a manifest dependency is already installed on this machine."""

from __future__ import annotations

from typing import Callable

from ..proc import CommandRunner
from .fragments import Dependency
from .packages import IPackageManager, LinuxPackageManager
from ..quiet_runner import quiet_runner
from .target import K_LINUX, target_for_platform


def check_cmd_ok(cmd: list[str], runner: CommandRunner | None = None) -> bool:
    """Return True if *cmd* runs through *runner* (the quiet runner when ``None``) and exits 0."""
    return (runner or quiet_runner()).capture(cmd)[0] == 0


def dep_installed(dep: Dependency, mgr: IPackageManager | None, platform: str,
                  vcpkg: IPackageManager | None = None,
                  runner: CommandRunner | None = None) -> bool:
    """Return whether *dep* is already installed on this platform; *runner* runs its check."""
    if dep.check_cmd and check_cmd_ok(dep.check_cmd, runner):
        return True
    return manager_holds(dep, mgr, platform, vcpkg)


def manager_holds(dep: Dependency, mgr: IPackageManager | None, platform: str,
                   vcpkg: IPackageManager | None = None) -> bool:
    """Return whether a package manager reports every package of *dep* installed."""
    pkgs = dep.packages_for(platform)
    if pkgs:
        return mgr is not None and all(mgr.is_installed(p) for p in pkgs)
    fallback = dep.vcpkg_fallback_ports(platform)
    if fallback:
        return vcpkg is not None and all(vcpkg.is_installed(p) for p in fallback)
    return False


def vcpkg_manager(managers: list[IPackageManager]) -> IPackageManager | None:
    """Return the vcpkg manager among *managers*, if wired in."""
    return named_manager(managers, "vcpkg")


def named_manager(managers: list[IPackageManager], name: str) -> IPackageManager | None:
    """Return the manager named *name* among *managers*, or None."""
    return next((m for m in managers if m.name == name), None)


def available_linux_manager(managers: list[IPackageManager]) -> LinuxPackageManager | None:
    """Return the Linux target's dependency manager among the distro managers of *managers*, or None."""
    distro = [m for m in managers if isinstance(m, LinuxPackageManager)]
    return target_for_platform(K_LINUX).dependency_manager(distro)


def dep_manager(managers: list[IPackageManager], platform: str) -> IPackageManager | None:
    """Return the manager that knows whether a manifest dependency is installed."""
    return target_for_platform(platform).dependency_manager(managers)


def held_by_managers(managers: list[IPackageManager],
                     platform: str) -> Callable[[Dependency], bool]:
    """Return the predicate telling whether *managers* report a dependency installed."""
    mgr = dep_manager(managers, platform)
    vcpkg = vcpkg_manager(managers)
    return lambda dep: manager_holds(dep, mgr, platform, vcpkg)
