# test_linux.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""How the Linux plan supplies the LLVM the acpp build needs."""

from __future__ import annotations

import pytest

from sushicore.provision.llvm_plan import LlvmRequest
from sushicore.provision.output_memory import MemoryConsole
from sushicore.provision.llvm_plans.linux import LinuxLlvmPlan
from sushicore.provision.packages.base_memory import InMemoryLinuxPackageManager


def _request(mgr) -> LlvmRequest:
    """Build a request that holds only the distro manager *mgr*."""
    return LlvmRequest(mgr=mgr, vcpkg=None, winget=None, assume_yes=False, llvm_bases=None,
                        console=MemoryConsole())


@pytest.mark.small
def test_no_distro_manager_leaves_the_build_without_llvm():
    """Check that a machine with no distro manager supplies no LLVM."""
    assert LinuxLlvmPlan().resolve(_request(None)) == (None, None)


@pytest.mark.small
def test_the_distro_manager_installs_the_build_dependencies():
    """Check that the manager is asked for the clang, llvm and boost packages."""
    manager = InMemoryLinuxPackageManager(name="apt")

    result = LinuxLlvmPlan().resolve(_request(manager))

    assert result == ("", None)
    assert manager.installs == [["clang", "llvm", "libboost-context-dev", "libboost-fiber-dev"]]
