# test_windows.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the Windows target."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from sushicore.provision.target import WindowsTarget


@pytest.mark.small
@pytest.mark.parametrize(("attribute", "expected"), [
    ("clang_executable", "clang++.exe"), ("nvcc_executable", "nvcc.exe"),
    ("python_executable", "python"), ("vcpkg_executable", "vcpkg.exe"),
    ("vcpkg_triplet", "x64-windows"), ("acpp_launcher", "acpp.bat"),
    ("intel_llvm_asset", "sycl_windows.tar.gz"), ("adapter_install_subdir", "bin"),
    ("searches_system_prefixes", False)])
def test_windows_target_names_its_files_and_triplet(attribute, expected):
    """Check that the Windows target answers PE file names and the Windows triplet."""
    assert getattr(WindowsTarget(), attribute) == expected


@pytest.mark.small
def test_windows_adapter_binary_is_a_dll():
    """Check that an adapter binary maps to its DLL name."""
    assert WindowsTarget().adapter_binary_patterns("ur_adapter") == ["ur_adapter.dll"]


@pytest.mark.small
def test_windows_adapter_build_names_clang_cl_and_lld_link(tmp_path):
    """Check that the adapter build is told the bundle's clang-cl and lld-link."""
    args = WindowsTarget().adapter_compiler_args(tmp_path)

    assert args == [f"-DCMAKE_C_COMPILER={tmp_path / 'bin' / 'clang-cl.exe'}",
                    f"-DCMAKE_CXX_COMPILER={tmp_path / 'bin' / 'clang-cl.exe'}",
                    f"-DCMAKE_LINKER={tmp_path / 'bin' / 'lld-link.exe'}"]


@pytest.mark.small
def test_windows_refuses_a_work_root_over_the_length_limit(tmp_path):
    """Check that a work root over 60 characters is refused with one warning."""
    warnings: list[str] = []
    root = tmp_path / ("x" * 80)

    assert (WindowsTarget().work_root_fits(root, warnings.append), len(warnings)) == (False, 1)


@pytest.mark.small
def test_windows_accepts_a_short_work_root():
    """Check that a short work root is accepted without a warning."""
    warnings: list[str] = []

    assert (WindowsTarget().work_root_fits(Path("C:/ur"), warnings.append), warnings) == (True, [])


@pytest.mark.small
def test_windows_finds_msvc_in_the_configured_vcvars(tmp_path, monkeypatch):
    """Check that a configured vcvars script that exists reports MSVC."""
    monkeypatch.delenv("VSINSTALLDIR", raising=False)
    vcvars = tmp_path / "vcvars64.bat"
    vcvars.write_text("")
    cfg = SimpleNamespace(vs_vcvars=str(vcvars), expand=lambda value: value)

    assert WindowsTarget().host_compilers(cfg) == [("MSVC", str(vcvars))]


@pytest.mark.small
def test_windows_finds_no_msvc_without_a_developer_shell_or_vcvars(monkeypatch):
    """Check that no compiler is reported when neither source names one."""
    monkeypatch.delenv("VSINSTALLDIR", raising=False)
    cfg = SimpleNamespace(vs_vcvars="", expand=lambda value: value)

    assert WindowsTarget().host_compilers(cfg) == []


@pytest.mark.small
def test_windows_has_no_vcpkg_fallback_ports():
    """Check that vcpkg is never a fallback on Windows."""
    assert WindowsTarget().vcpkg_fallback_ports([], ["hwloc"]) == []


@pytest.mark.small
def test_windows_bootstraps_vcpkg_through_cmd(tmp_path):
    """Check that the bootstrap batch file runs through cmd and its code is returned."""
    seen: list[list[str]] = []

    def drain(command, dry_run):
        seen.append(command)
        return 7

    code = WindowsTarget().bootstrap_vcpkg(tmp_path, drain, False)

    assert (code, seen) == (7, [["cmd", "/c", str(tmp_path / "bootstrap-vcpkg.bat"),
                                 "-disableMetrics"]])


@pytest.mark.small
def test_windows_dependency_manager_is_vcpkg_even_when_not_available():
    """Check that Windows asks vcpkg and nothing else about a manifest dependency."""
    vcpkg = SimpleNamespace(name="vcpkg", available=lambda: False)
    winget = SimpleNamespace(name="winget", available=lambda: True)

    assert WindowsTarget().dependency_manager([winget, vcpkg]) is vcpkg


@pytest.mark.small
def test_windows_puts_the_sdk_resource_compiler_directory_in_front_of_the_acpp_path():
    """Check that the rc.exe directory leads PATH."""
    env = {"PATH": "C:/bin"}

    WindowsTarget().prepare_acpp_environment(env, lambda: "C:/sdk")

    assert env["PATH"].startswith("C:/sdk")


@pytest.mark.small
def test_windows_acpp_configure_passes_the_vcpkg_toolchain_file_only_when_present(tmp_path):
    """Check that an existing toolchain file becomes a cmake argument and a missing one does not."""
    present = tmp_path / "vcpkg.cmake"
    present.write_text("")

    target = WindowsTarget()

    assert (target.acpp_configure_args(present), target.acpp_configure_args(tmp_path / "no")) == (
        [f"-DCMAKE_TOOLCHAIN_FILE={present}"], [])
