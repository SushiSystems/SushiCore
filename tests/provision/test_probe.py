# test_probe.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests for tool probing."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from sushicore.provision import probe
from sushicore.provision.config import ProvisionSettings


def test_classify_prefers_a_discrete_adapter():
    """Check that classification prefers a discrete adapter."""
    adapters = "Intel(R) UHD Graphics 770\nNVIDIA GeForce RTX 4070\n"
    assert probe.classify_display_adapters(adapters) == "nvidia"


def test_integrated_only_falls_back_to_its_vendor():
    """Check that integrated-only falls back to its vendor."""
    assert probe.classify_display_adapters("Intel(R) UHD Graphics 770\n") == "intel"


def test_binary_works_rejects_a_missing_command():
    """Check that binary_works rejects a missing command."""
    assert probe.binary_works("sushi-no-such-binary-xyz") is False


def test_tools_dir_follows_the_root(provision_home):
    """Check that tools_dir follows the root."""
    assert probe._tools_dir() == provision_home.resolve() / "tools"


def _vs_tree(root, year, edition):
    bat = root / "Microsoft Visual Studio" / year / edition / "VC" / "Auxiliary" / "Build"
    bat.mkdir(parents=True)
    (bat / "vcvars64.bat").write_text("")
    return bat / "vcvars64.bat"


def _no_vswhere(monkeypatch):
    monkeypatch.setattr(probe, "_vcvars_from_vswhere", lambda: None)
    monkeypatch.setattr(probe.sys, "platform", "win32")


def test_find_vcvars_is_none_off_windows(monkeypatch):
    monkeypatch.setattr(probe.sys, "platform", "linux")
    assert probe.find_vcvars() is None


def test_find_vcvars_scans_the_newest_year_first(monkeypatch, tmp_path):
    _no_vswhere(monkeypatch)
    _vs_tree(tmp_path, "2019", "Community")
    newest = _vs_tree(tmp_path, "2026", "BuildTools")
    monkeypatch.setenv("ProgramFiles", str(tmp_path))
    monkeypatch.delenv("ProgramFiles(x86)", raising=False)
    assert probe.find_vcvars() == newest


def test_find_vcvars_prefers_vswhere(monkeypatch, tmp_path):
    monkeypatch.setattr(probe.sys, "platform", "win32")
    hit = tmp_path / "vcvars64.bat"
    monkeypatch.setattr(probe, "_vcvars_from_vswhere", lambda: hit)
    assert probe.find_vcvars() == hit


def test_find_vcvars_is_none_when_nothing_is_installed(monkeypatch, tmp_path):
    _no_vswhere(monkeypatch)
    monkeypatch.setenv("ProgramFiles", str(tmp_path))
    monkeypatch.delenv("ProgramFiles(x86)", raising=False)
    assert probe.find_vcvars() is None


def test_resolve_windows_keeps_the_2022_glob_first(monkeypatch):
    from types import SimpleNamespace
    monkeypatch.setattr(probe, "_first_glob", lambda patterns: "C:/VS/2022/x.bat")
    monkeypatch.setattr(probe, "find_vcvars", lambda: None)
    cfg = SimpleNamespace(vs_vcvars="", oneapi_root="", vcpkg_root="", vcpkg_triplet="",
                          llvm_root="", acpp_exe="", platform="windows",
                          expand=lambda s: s)
    assert probe._resolve_windows(cfg)["vs_vcvars"] == "C:/VS/2022/x.bat"


def test_resolve_windows_falls_back_to_find_vcvars(monkeypatch, tmp_path):
    from types import SimpleNamespace
    hit = tmp_path / "vcvars64.bat"
    monkeypatch.setattr(probe, "_first_glob", lambda patterns: "")
    monkeypatch.setattr(probe, "find_vcvars", lambda: hit)
    cfg = SimpleNamespace(vs_vcvars="", oneapi_root="", vcpkg_root="", vcpkg_triplet="",
                          llvm_root="", acpp_exe="", platform="windows",
                          expand=lambda s: s)
    assert probe._resolve_windows(cfg)["vs_vcvars"] == str(hit)


_CLANG = Path("bin") / "clang++"


def _bundle(root):
    """Create an llvm-sycl bundle holding a clang++ under *root* and return the file."""
    exe = root / "toolchains" / "llvm-sycl" / _CLANG
    exe.parent.mkdir(parents=True)
    exe.write_text("")
    return exe


def test_installed_toolchain_prefers_the_current_root(provision_home, tmp_path, monkeypatch):
    """Check that installed toolchain prefers the current root."""
    legacy = tmp_path / "legacy"
    monkeypatch.setenv("SUSHISTACK_DEPS_DIR", str(legacy))
    _bundle(legacy)
    current = _bundle(provision_home)
    assert probe.installed_toolchain("llvm-sycl", _CLANG) == current.resolve()


def test_installed_toolchain_falls_back_to_a_legacy_root(provision_home, tmp_path, monkeypatch):
    """Check that installed toolchain falls back to a legacy root."""
    legacy = tmp_path / "legacy"
    monkeypatch.setenv("SUSHISTACK_DEPS_DIR", str(legacy))
    exe = _bundle(legacy)
    assert probe.installed_toolchain("llvm-sycl", _CLANG) == exe.resolve()


def test_installed_toolchain_is_none_when_no_root_holds_it(provision_home):
    """Check that installed toolchain is none when no root holds it."""
    assert probe.installed_toolchain("llvm-sycl", _CLANG) is None


def test_discovery_records_a_legacy_bundle(provision_home, tmp_path, monkeypatch):
    """Check that discovery records a legacy bundle."""
    legacy = tmp_path / "legacy"
    monkeypatch.setenv("SUSHISTACK_DEPS_DIR", str(legacy))
    _bundle(legacy)
    values: dict[str, str] = {}
    probe._discover_installed_toolchains(ProvisionSettings(platform="linux"), values)
    assert values["llvm_root"] == str((legacy / "toolchains" / "llvm-sycl").resolve())



def _failing_run(monkeypatch, error: Exception) -> None:
    """Make every ``subprocess.run`` the probe starts raise *error*."""
    def run(*_args, **_kwargs):
        """Raise the configured error in place of running a process."""
        raise error
    monkeypatch.setattr(probe.subprocess, "run", run)


def _probe_records(caplog, level: str) -> list[str]:
    """Return the messages the provision logger recorded at *level*."""
    return [r.getMessage() for r in caplog.records
            if r.name == "sushicore.provision" and r.levelname == level]


def test_a_missing_lspci_is_recorded(monkeypatch, caplog):
    """Check that an lspci that cannot start yields no adapters and one warning."""
    _failing_run(monkeypatch, FileNotFoundError("lspci"))
    with caplog.at_level("WARNING", logger="sushicore.provision"):
        assert probe._linux_display_adapters() == ""
    assert len(_probe_records(caplog, "WARNING")) == 1
    assert "lspci" in _probe_records(caplog, "WARNING")[0]


def test_a_video_controller_query_that_times_out_is_recorded(monkeypatch, caplog):
    """Check that a PowerShell query that times out yields no adapters and one warning."""
    _failing_run(monkeypatch, subprocess.TimeoutExpired("powershell", 30))
    with caplog.at_level("WARNING", logger="sushicore.provision"):
        assert probe._windows_display_adapters() == ""
    assert len(_probe_records(caplog, "WARNING")) == 1
    assert "timed out" in _probe_records(caplog, "WARNING")[0]


@pytest.mark.parametrize("reader", ["_linux_display_adapters", "_windows_display_adapters"])
def test_a_defect_in_an_adapter_query_is_not_reported_as_no_adapters(monkeypatch, reader):
    """Check that an error no process raises escapes the adapter readers."""
    _failing_run(monkeypatch, TypeError("defect"))
    with pytest.raises(TypeError):
        getattr(probe, reader)()


def test_binary_works_records_why_a_command_did_not_run(monkeypatch, caplog):
    """Check that binary_works logs the error behind a False answer."""
    _failing_run(monkeypatch, PermissionError(13, "Access is denied"))
    with caplog.at_level("DEBUG", logger="sushicore.provision"):
        assert probe.binary_works("cmake") is False
    assert len(_probe_records(caplog, "DEBUG")) == 1
    assert "cmake" in _probe_records(caplog, "DEBUG")[0]


def test_binary_works_does_not_report_a_defect_as_a_broken_binary(monkeypatch):
    """Check that an error no process raises escapes binary_works."""
    _failing_run(monkeypatch, TypeError("defect"))
    with pytest.raises(TypeError):
        probe.binary_works("cmake")
