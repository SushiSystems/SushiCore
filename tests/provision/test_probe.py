# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for tool probing."""

from __future__ import annotations

from sushicore.provision import probe


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
