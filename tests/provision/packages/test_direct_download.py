# test_direct_download.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The direct installers replace their folder, ask for their asset and warn on a refused PATH."""

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


def _fetch_archive(member: str):
    """Return a download transport that writes a one-member archive in place of a download."""
    def fetch(_url: str, dest: Path) -> None:
        """Write the archive the real transport would have fetched."""
        _write_zip(dest, member)
    return fetch


def _asked_for(asked: list[tuple[str, str]]):
    """Return an asset resolver that records the repository and glob it is asked for."""
    def resolve(repo: str, glob: str) -> str:
        """Record the request and answer a fixed URL."""
        asked.append((repo, glob))
        return "https://example.invalid/a.zip"
    return resolve


@pytest.mark.medium
@pytest.mark.parametrize(("installer", "member", "folder", "exe"), [
    ("_install_cmake_direct", "cmake-1.0/bin/cmake.exe", "cmake", ("bin", "cmake.exe")),
    ("_install_doxygen_direct", "doxygen-1.0/doxygen.exe", "doxygen", ("doxygen.exe",)),
])
def test_a_direct_install_replaces_the_previous_folder(
        installer, member, folder, exe, provision_home, recording_console):
    """Check that an install drops the stale files of the old folder and puts the program in."""
    target = dd.tools_dir() / folder
    target.mkdir(parents=True)
    (target / "stale.txt").write_text("stale")
    options = {"cmake_on_system": lambda: ""} if folder == "cmake" else {}

    installed = getattr(dd, installer)(
        resolve_asset=_asked_for([]), fetch=_fetch_archive(member), on_path=lambda _dir: None,
        **options)

    assert installed is True
    assert not (target / "stale.txt").exists()
    assert target.joinpath(*exe).is_file()


@pytest.mark.medium
def test_ninja_direct_install_puts_ninja_in_the_tools_folder(provision_home, recording_console):
    """Check that the ninja archive's executable lands in the tools folder."""
    installed = dd._install_ninja_direct(
        resolve_asset=_asked_for([]), fetch=_fetch_archive("ninja.exe"),
        on_path=lambda _dir: None)
    assert installed is True
    assert (dd.tools_dir() / "ninja.exe").is_file()


K_ASSETS = [
    ("_install_cmake_direct", "cmake-1.0/bin/cmake.exe", "Kitware/CMake", "*windows-x86_64.zip"),
    ("_install_ninja_direct", "ninja.exe", "ninja-build/ninja", "ninja-win.zip"),
    ("_install_doxygen_direct", "doxygen-1.0/doxygen.exe", "doxygen/doxygen",
     "doxygen-*.windows.x64.bin.zip"),
]


@pytest.mark.medium
@pytest.mark.parametrize(("installer", "member", "repo", "glob"), K_ASSETS)
def test_a_direct_install_asks_for_its_own_github_asset(
        installer, member, repo, glob, provision_home, recording_console):
    """Check that each installer asks the release resolver for its repository and asset glob."""
    asked: list[tuple[str, str]] = []
    options = {"cmake_on_system": lambda: ""} if installer == "_install_cmake_direct" else {}
    getattr(dd, installer)(
        resolve_asset=_asked_for(asked), fetch=_fetch_archive(member),
        on_path=lambda _dir: None, **options)
    assert asked == [(repo, glob)]


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


def _run_direct_install(installer: str, member: str, path_written: bool) -> bool:
    """Run *installer* against a one-member archive; the user PATH write answers *path_written*."""
    options = {"cmake_on_system": lambda: ""} if installer == "_install_cmake_direct" else {}
    return getattr(dd, installer)(
        resolve_asset=_asked_for([]), fetch=_fetch_archive(member),
        on_path=lambda directory: dd._put_on_user_path(
            directory, add_to_path=lambda _directory: path_written),
        **options)


@pytest.mark.medium
@pytest.mark.parametrize("path_written", [False, True])
@pytest.mark.parametrize(("installer", "member", "path_parts"), K_DIRECT_INSTALLS)
def test_direct_install_warns_only_when_the_user_path_write_is_refused(
        installer, member, path_parts, path_written, provision_home, recording_console):
    """Check that a refused user PATH write warns once, a stored one stays quiet, both install."""
    assert _run_direct_install(installer, member, path_written) is True
    warnings = recording_console.texts("warn")
    if path_written:
        assert warnings == []
    else:
        assert len(warnings) == 1
        assert str(dd.tools_dir().joinpath(*path_parts)) in warnings[0]
