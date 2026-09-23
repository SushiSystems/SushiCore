# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""The direct-download installers only remove paths under the bound dependency root."""

from __future__ import annotations

import zipfile
from pathlib import Path

from sushicore.provision.packages import direct_download as dd


def _write_zip(path: Path, member: str) -> None:
    """Write a single-entry zip archive to *path*."""
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr(member, b"")


def _recording_rmtree(target: Path, monkeypatch, removed: list[Path]) -> None:
    """Wrap ``shutil.rmtree`` to record every call for *target* without swallowing it.

    Only the *target* call is recorded: ``tempfile.TemporaryDirectory`` also calls
    ``shutil.rmtree`` on its own staging directory through the same module, and that
    call is unrelated to the safety question this test asks.
    """
    real_rmtree = dd.shutil.rmtree

    def recording(path, *args, **kwargs):
        """Check that recording."""
        if Path(path) == target:
            removed.append(Path(path))
        return real_rmtree(path, *args, **kwargs)

    monkeypatch.setattr(dd.shutil, "rmtree", recording)


def test_cmake_direct_install_only_removes_paths_under_the_bound_root(
        tmp_path, monkeypatch, provision_home, recording_console):
    """Check that cmake direct install only removes paths under the bound root."""
    monkeypatch.setattr(dd, "_cmake_on_system", lambda: "")
    monkeypatch.setattr(dd, "gh_latest_asset", lambda repo, glob: "https://example.invalid/c.zip")
    monkeypatch.setattr(dd, "download",
                         lambda url, dest: _write_zip(dest, "cmake-1.0/bin/cmake.exe"))
    monkeypatch.setattr(dd, "_add_to_user_path_windows", lambda directory: None)

    target = dd.tools_dir() / "cmake"
    target.mkdir(parents=True)
    (target / "stale.txt").write_text("stale")

    removed: list[Path] = []
    _recording_rmtree(target, monkeypatch, removed)

    assert dd._install_cmake_direct() is True
    assert removed == [target]
    assert target.is_relative_to(tmp_path)
    assert (dd.tools_dir() / "cmake" / "bin" / "cmake.exe").is_file()


def test_doxygen_direct_install_only_removes_paths_under_the_bound_root(
        tmp_path, monkeypatch, provision_home, recording_console):
    """Check that doxygen direct install only removes paths under the bound root."""
    monkeypatch.setattr(dd, "gh_latest_asset", lambda repo, glob: "https://example.invalid/d.zip")
    monkeypatch.setattr(dd, "download",
                         lambda url, dest: _write_zip(dest, "doxygen-1.0/doxygen.exe"))
    monkeypatch.setattr(dd, "_add_to_user_path_windows", lambda directory: None)

    target = dd.tools_dir() / "doxygen"
    target.mkdir(parents=True)
    (target / "stale.txt").write_text("stale")

    removed: list[Path] = []
    _recording_rmtree(target, monkeypatch, removed)

    assert dd._install_doxygen_direct() is True
    assert removed == [target]
    assert target.is_relative_to(tmp_path)
    assert (dd.tools_dir() / "doxygen" / "doxygen.exe").is_file()
