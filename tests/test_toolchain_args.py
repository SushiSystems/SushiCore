# test_toolchain_args.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The two pieces of toolchain-flag assembly that carry no module policy."""

from pathlib import Path

import pytest

from sushicore.stack_config import StackConfig
from sushicore.toolchain_args import c_compiler_for, vcpkg_prefix


pytestmark = pytest.mark.medium


def test_a_clangxx_gets_its_sibling_clang(tmp_path):
    """clang++ hardcodes C++ mode, which breaks CMake's C-language probe."""
    (tmp_path / "clang").write_text("")
    cxx = tmp_path / "clang++"
    cxx.write_text("")
    assert c_compiler_for(str(cxx)) == str(tmp_path / "clang")


def test_an_icpx_gets_its_sibling_icx(tmp_path):
    """icpx is oneAPI's C++ driver; CMake's C-language probe needs the icx beside it."""
    (tmp_path / "icx").write_text("")
    cxx = tmp_path / "icpx"
    cxx.write_text("")
    assert c_compiler_for(str(cxx)) == str(tmp_path / "icx")


def test_a_bare_icpx_gets_icx_from_the_path(tmp_path, monkeypatch):
    """A package build hands over the name the PATH resolves, not a path."""
    (tmp_path / "icx").write_text("")
    monkeypatch.setattr("shutil.which", lambda name: str(tmp_path / name) if name == "icx" else None)
    assert c_compiler_for("icpx") == str(tmp_path / "icx")


@pytest.mark.parametrize("cxx", ["/nowhere/clang++", "/usr/bin/g++"])
def test_a_compiler_with_no_sibling_is_left_alone(cxx):
    """A compiler without a sibling C driver is returned unchanged."""
    assert c_compiler_for(cxx) == cxx


def test_the_windows_exe_suffix_is_preserved(tmp_path):
    (tmp_path / "clang.exe").write_text("")
    cxx = tmp_path / "clang++.exe"
    cxx.write_text("")
    assert c_compiler_for(str(cxx)) == str(tmp_path / "clang.exe")


def test_vcpkg_prefix_is_empty_without_a_root():
    """A config that turns vcpkg off has no prefix."""
    assert vcpkg_prefix(StackConfig(platform="linux", use_vcpkg=False), Path(".")) == ""


def test_vcpkg_prefix_names_the_triplet():
    """The prefix is the vcpkg root, installed, then the triplet."""
    cfg = StackConfig(platform="windows", vcpkg_root="C:/vcpkg", vcpkg_triplet="x64-windows")
    assert vcpkg_prefix(cfg, Path(".")) == "C:/vcpkg/installed/x64-windows"
