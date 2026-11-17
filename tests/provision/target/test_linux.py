# test_linux.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the Linux target."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from sushicore.provision.target import LinuxTarget


@pytest.mark.small
@pytest.mark.parametrize(("attribute", "expected"), [
    ("clang_executable", "clang++"), ("nvcc_executable", "nvcc"),
    ("python_executable", "python3"), ("vcpkg_executable", "vcpkg"),
    ("vcpkg_triplet", "x64-linux"), ("acpp_launcher", "acpp"),
    ("intel_llvm_asset", "sycl_linux.tar.gz"), ("adapter_install_subdir", "lib"),
    ("searches_system_prefixes", True)])
def test_linux_target_names_its_files_and_triplet(attribute, expected):
    """Check that the Linux target answers ELF file names and the Linux triplet."""
    assert getattr(LinuxTarget(), attribute) == expected


@pytest.mark.small
def test_linux_adapter_binary_is_a_versioned_shared_object():
    """Check that an adapter binary maps to its shared-object glob."""
    assert LinuxTarget().adapter_binary_patterns("ur_adapter") == ["libur_adapter.so*"]


@pytest.mark.small
def test_linux_adapter_build_adds_no_compiler_arguments(tmp_path):
    """Check that the adapter build keeps the default compiler."""
    assert LinuxTarget().adapter_compiler_args(tmp_path) == []


@pytest.mark.small
def test_linux_accepts_any_work_root(tmp_path):
    """Check that no work root length is refused."""
    assert LinuxTarget().work_root_fits(tmp_path / ("x" * 200), lambda _line: None) is True


@pytest.mark.small
def test_linux_vcpkg_covers_only_a_dependency_without_distro_packages():
    """Check that vcpkg ports apply when and only when no apt package is named."""
    target = LinuxTarget()

    assert (target.vcpkg_fallback_ports([], ["hwloc"]),
            target.vcpkg_fallback_ports(["libhwloc-dev"], ["hwloc"])) == (["hwloc"], [])


@pytest.mark.small
def test_linux_dependency_manager_takes_apt_over_dnf_when_both_are_available():
    """Check that the first available manager in the apt, dnf order is the one chosen."""
    apt = SimpleNamespace(name="apt", available=lambda: True)
    dnf = SimpleNamespace(name="dnf", available=lambda: True)

    assert LinuxTarget().dependency_manager([dnf, apt]) is apt


@pytest.mark.small
def test_linux_dependency_manager_skips_a_manager_that_is_not_available():
    """Check that an unavailable apt leaves dnf as the answer."""
    apt = SimpleNamespace(name="apt", available=lambda: False)
    dnf = SimpleNamespace(name="dnf", available=lambda: True)

    assert LinuxTarget().dependency_manager([apt, dnf]) is dnf


@pytest.mark.small
def test_linux_bootstrap_runs_the_script_and_returns_its_exit_code(tmp_path):
    """Check that a dry run runs the script as named and returns the drain's code."""
    seen: list[list[str]] = []

    def drain(command, dry_run):
        seen.append(command)
        return 3

    code = LinuxTarget().bootstrap_vcpkg(tmp_path, drain, True)

    assert (code, seen) == (3, [[str(tmp_path / "bootstrap-vcpkg.sh"), "-disableMetrics"]])


@pytest.mark.small
def test_linux_acpp_needs_no_environment_change():
    """Check that the acpp build environment is left as it was."""
    env = {"PATH": "/bin"}

    LinuxTarget().prepare_acpp_environment(env, lambda: "/never")

    assert env == {"PATH": "/bin"}
