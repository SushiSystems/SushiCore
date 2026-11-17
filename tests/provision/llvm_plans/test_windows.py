# test_windows.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""How the Windows plan finds, installs and vendors the LLVM the acpp build needs."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.provision.llvm_plan import LlvmRequest
from sushicore.provision.llvm_plans.windows import WindowsLlvmPlan, find_windows_llvm, llvm_missing
from sushicore.provision.output_memory import MemoryConsole
from sushicore.provision.packages.base_memory import InMemoryPackageManager


def _llvm_tree(root: Path) -> Path:
    """Create the cmake folder an LLVM install holds under *root* and return it."""
    cmake_dir = root / "lib" / "cmake" / "llvm"
    cmake_dir.mkdir(parents=True)
    return cmake_dir


def _request(**overrides) -> LlvmRequest:
    """Build a request with nothing available and no consent, with *overrides* applied."""
    fields = {"mgr": None, "vcpkg": None, "winget": None, "assume_yes": False, "llvm_bases": [],
              "console": MemoryConsole()}
    return LlvmRequest(**{**fields, **overrides})


@pytest.mark.medium
def test_the_first_base_holding_an_llvm_cmake_folder_wins(tmp_path):
    """Check that the lookup returns the cmake folder and the prefix of the first base that has one."""
    first, second = tmp_path / "first", tmp_path / "second"
    cmake_dir = _llvm_tree(first)
    _llvm_tree(second)

    assert find_windows_llvm([first, second]) == (str(cmake_dir), str(first))


@pytest.mark.small
def test_no_base_holding_an_llvm_is_a_missing_llvm():
    """Check that an empty list of bases reports the LLVM as missing."""
    assert llvm_missing([]) is True


@pytest.mark.medium
def test_an_existing_llvm_is_reused_after_vcpkg_installs_boost(tmp_path):
    """Check that vcpkg is asked for boost and the LLVM already on disk is the answer."""
    cmake_dir = _llvm_tree(tmp_path / "llvm")
    vcpkg = InMemoryPackageManager(name="vcpkg")

    result = WindowsLlvmPlan().resolve(_request(vcpkg=vcpkg, llvm_bases=[tmp_path / "llvm"]))

    assert result == (str(cmake_dir), str(tmp_path / "llvm"))
    assert vcpkg.installs == [["boost-context", "boost-fiber"]]


@pytest.mark.small
def test_a_missing_llvm_is_not_downloaded_without_consent():
    """Check that no consent leaves the build without LLVM and installs nothing."""
    winget = InMemoryPackageManager(name="winget")

    assert WindowsLlvmPlan().resolve(_request(winget=winget)) == (None, None)
    assert winget.installs == []
