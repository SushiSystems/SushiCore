# test_direct_download.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The direct-download installers only remove paths under the bound dependency root."""

from __future__ import annotations

import os
import types
import zipfile
from pathlib import Path

import pytest

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


@pytest.mark.medium
def test_cmake_direct_install_only_removes_paths_under_the_bound_root(
        tmp_path, monkeypatch, provision_home, recording_console):
    """Check that cmake direct install only removes paths under the bound root."""
    monkeypatch.setattr(dd, "_cmake_on_system", lambda: "")
    monkeypatch.setattr(dd, "gh_latest_asset", lambda repo, glob: "https://example.invalid/c.zip")
    monkeypatch.setattr(dd, "download",
                         lambda url, dest: _write_zip(dest, "cmake-1.0/bin/cmake.exe"))
    monkeypatch.setattr(dd, "_add_to_user_path_windows", lambda directory: True)

    target = dd.tools_dir() / "cmake"
    target.mkdir(parents=True)
    (target / "stale.txt").write_text("stale")

    removed: list[Path] = []
    _recording_rmtree(target, monkeypatch, removed)

    assert dd._install_cmake_direct() is True
    assert removed == [target]
    assert target.is_relative_to(tmp_path)
    assert (dd.tools_dir() / "cmake" / "bin" / "cmake.exe").is_file()


@pytest.mark.medium
def test_doxygen_direct_install_only_removes_paths_under_the_bound_root(
        tmp_path, monkeypatch, provision_home, recording_console):
    """Check that doxygen direct install only removes paths under the bound root."""
    monkeypatch.setattr(dd, "gh_latest_asset", lambda repo, glob: "https://example.invalid/d.zip")
    monkeypatch.setattr(dd, "download",
                         lambda url, dest: _write_zip(dest, "doxygen-1.0/doxygen.exe"))
    monkeypatch.setattr(dd, "_add_to_user_path_windows", lambda directory: True)

    target = dd.tools_dir() / "doxygen"
    target.mkdir(parents=True)
    (target / "stale.txt").write_text("stale")

    removed: list[Path] = []
    _recording_rmtree(target, monkeypatch, removed)

    assert dd._install_doxygen_direct() is True
    assert removed == [target]
    assert target.is_relative_to(tmp_path)
    assert (dd.tools_dir() / "doxygen" / "doxygen.exe").is_file()



def _winreg(open_key):
    """Return the calls of ``winreg`` with *open_key* as ``OpenKey``, and the values it stores."""
    stored: dict[str, str] = {}

    def query(_key, name):
        """Return the stored value the way ``QueryValueEx`` does."""
        if name not in stored:
            raise FileNotFoundError(name)
        return stored[name], 2

    def store(_key, name, _reserved, _kind, value):
        """Record the value ``SetValueEx`` was asked to write."""
        stored[name] = value

    module = types.SimpleNamespace(
        HKEY_CURRENT_USER=1, KEY_READ=1, KEY_WRITE=2, REG_EXPAND_SZ=2,
        OpenKey=open_key, QueryValueEx=query, SetValueEx=store, CloseKey=lambda _key: None,
    )
    return module, stored


def _raising(error: Exception):
    """Return an ``OpenKey`` that raises *error*."""
    def open_key(*_args):
        """Raise the configured error in place of opening the key."""
        raise error
    return open_key


def _refused_write(caplog):
    """Run a PATH write the registry refuses; return the result, the warnings and the environment."""
    module, _stored = _winreg(_raising(PermissionError(5, "Access is denied")))
    environ = {"PATH": "C:/base"}
    with caplog.at_level("WARNING", logger="sushicore.provision"):
        result = dd._add_to_user_path_windows("C:/tools", module, environ)
    warnings = [r.getMessage() for r in caplog.records
                if r.name.startswith("sushicore.provision") and r.levelname == "WARNING"]
    return result, warnings, environ


@pytest.mark.small
def test_a_refused_user_path_write_returns_false(caplog):
    """Check that a refused registry write answers False."""
    assert _refused_write(caplog)[0] is False


@pytest.mark.small
def test_a_refused_user_path_write_is_recorded_naming_the_directory(caplog):
    """Check that a refused registry write logs one warning that names the directory."""
    warnings = _refused_write(caplog)[1]
    assert len(warnings) == 1 and "C:/tools" in warnings[0]


@pytest.mark.small
def test_a_refused_user_path_write_still_serves_this_process(caplog):
    """Check that this process finds the directory on its PATH although the registry refused."""
    assert _refused_write(caplog)[2]["PATH"] == os.pathsep.join(["C:/base", "C:/tools"])


@pytest.mark.small
def test_a_user_path_write_that_lands_reports_success():
    """Check that a stored PATH value returns True and reaches this process."""
    module, stored = _winreg(lambda *_args: object())
    environ = {"PATH": "C:/base"}
    assert dd._add_to_user_path_windows("C:/tools", module, environ) is True
    assert stored == {"Path": "C:/tools"}
    assert environ["PATH"] == os.pathsep.join(["C:/base", "C:/tools"])


@pytest.mark.small
def test_a_defect_in_the_user_path_write_is_not_swallowed():
    """Check that an error the registry does not raise escapes the PATH write."""
    module, _stored = _winreg(_raising(TypeError("defect")))
    with pytest.raises(TypeError):
        dd._add_to_user_path_windows("C:/tools", module, {"PATH": ""})


K_DIRECT_INSTALLS = [
    ("_install_cmake_direct", "cmake-1.0/bin/cmake.exe", ("cmake", "bin")),
    ("_install_ninja_direct", "ninja.exe", ()),
    ("_install_doxygen_direct", "doxygen-1.0/doxygen.exe", ("doxygen",)),
]


def _run_direct_install(monkeypatch, installer: str, member: str, path_written: bool) -> bool:
    """Run *installer* against a one-member archive with the user PATH write stubbed."""
    monkeypatch.setattr(dd, "_cmake_on_system", lambda: "")
    monkeypatch.setattr(dd, "gh_latest_asset", lambda repo, glob: "https://example.invalid/a.zip")
    monkeypatch.setattr(dd, "download", lambda url, dest: _write_zip(dest, member))
    monkeypatch.setattr(dd, "_add_to_user_path_windows", lambda directory: path_written)
    return getattr(dd, installer)()


@pytest.mark.medium
@pytest.mark.parametrize(("installer", "member", "path_parts"), K_DIRECT_INSTALLS)
def test_direct_install_warns_when_the_user_path_write_is_refused(
        installer, member, path_parts, monkeypatch, provision_home, recording_console):
    """Check that a refused user PATH write reaches the console and the install still succeeds."""
    assert _run_direct_install(monkeypatch, installer, member, path_written=False) is True
    warnings = [args[0] for name, args in recording_console.calls if name == "warn"]
    assert len(warnings) == 1
    assert str(dd.tools_dir().joinpath(*path_parts)) in warnings[0]


@pytest.mark.medium
@pytest.mark.parametrize(("installer", "member", "path_parts"), K_DIRECT_INSTALLS)
def test_direct_install_stays_quiet_when_the_user_path_write_lands(
        installer, member, path_parts, monkeypatch, provision_home, recording_console):
    """Check that a stored user PATH value draws no warning."""
    assert _run_direct_install(monkeypatch, installer, member, path_written=True) is True
    assert [name for name, _args in recording_console.calls if name == "warn"] == []
