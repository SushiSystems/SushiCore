# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Installs cmake, ninja, git and doxygen on Windows via direct GitHub downloads."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import urllib.request
import zipfile
from pathlib import Path
from typing import Callable

from .. import home
from .._output import console
from ..probe import binary_works
from ..system import USER_AGENT
from .base import IPackageManager, refresh_windows_path
from .github_release import gh_latest_asset


def tools_dir() -> Path:
    """Return the directory where portable tools (cmake, ninja) install."""
    return home.tools_dir()


def download(url: str, dest: Path) -> None:
    """Fetch *url* into *dest*, streaming the response in chunks."""
    console.info(f"Downloading {dest.name} ...")
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=300) as resp, open(dest, "wb") as fh:
        while chunk := resp.read(1 << 16):
            fh.write(chunk)


def _add_to_user_path_windows(directory: str) -> None:
    """Persistently append *directory* to the current user's PATH registry key."""
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, r"Environment",
            0, winreg.KEY_READ | winreg.KEY_WRITE,
        )
        try:
            current, _ = winreg.QueryValueEx(key, "Path")
        except FileNotFoundError:
            current = ""
        if directory.lower() not in current.lower():
            new_path = f"{current};{directory}" if current else directory
            winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, new_path)
        winreg.CloseKey(key)
        os.environ["PATH"] = os.environ.get("PATH", "") + os.pathsep + directory
    except Exception:
        pass


def _cmake_portable_bin() -> Path:
    """Return the bin/ directory of the portable CMake the direct-download manager extracts."""
    return tools_dir() / "cmake" / "bin"


def _cmake_on_system() -> str:
    """Resolve a usable cmake after a refresh: PATH, Program Files, portable dir."""
    refresh_windows_path()
    found = shutil.which("cmake")
    if found:
        return found
    candidates = [
        r"C:\Program Files\CMake\bin\cmake.exe",
        r"C:\Program Files (x86)\CMake\bin\cmake.exe",
        str(_cmake_portable_bin() / "cmake.exe"),
    ]
    for base in candidates:
        if Path(base).is_file():
            return base
    return ""


def _install_cmake_direct() -> bool:
    """Extract the portable CMake zip into the tools dir and add it to PATH."""
    if _cmake_on_system():
        console.info("cmake: already present, skipping.")
        return True
    try:
        url = gh_latest_asset("Kitware/CMake", "*windows-x86_64.zip")
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as f:
            zip_dest = Path(f.name)
        download(url, zip_dest)
        target = tools_dir() / "cmake"
        console.info(f"Extracting CMake to {target} ...")
        with tempfile.TemporaryDirectory() as staging:
            stage = Path(staging)
            with zipfile.ZipFile(zip_dest) as zf:
                zf.extractall(stage)
            entries = list(stage.iterdir())
            srcroot = entries[0] if len(entries) == 1 and entries[0].is_dir() else stage
            if target.exists():
                shutil.rmtree(target, ignore_errors=True)
            shutil.move(str(srcroot), str(target))
        zip_dest.unlink(missing_ok=True)
        _add_to_user_path_windows(str(_cmake_portable_bin()))
        if (_cmake_portable_bin() / "cmake.exe").is_file():
            return True
        console.error("CMake not found after extracting the portable archive.")
        return False
    except Exception as exc:
        console.error(f"CMake direct install failed: {exc}")
        return False


def _install_ninja_direct() -> bool:
    """Extract the ninja.exe archive into the tools dir and add it to PATH."""
    try:
        url = gh_latest_asset("ninja-build/ninja", "ninja-win.zip")
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as f:
            dest = Path(f.name)
        download(url, dest)
        tools = tools_dir()
        tools.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(dest) as zf:
            zf.extract("ninja.exe", tools)
        dest.unlink(missing_ok=True)
        _add_to_user_path_windows(str(tools))
        return (tools / "ninja.exe").is_file()
    except Exception as exc:
        console.error(f"Ninja direct install failed: {exc}")
        return False


def _install_doxygen_direct() -> bool:
    """Extract the portable Doxygen zip into the tools dir and add it to PATH."""
    target = tools_dir() / "doxygen"
    exe = target / "doxygen.exe"
    if exe.is_file():
        console.info("doxygen: already present in deps/tools, skipping.")
        return True
    try:
        url = gh_latest_asset("doxygen/doxygen", "doxygen-*.windows.x64.bin.zip")
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as f:
            zip_dest = Path(f.name)
        download(url, zip_dest)
        console.info(f"Extracting Doxygen to {target} ...")
        with tempfile.TemporaryDirectory() as staging:
            stage = Path(staging)
            with zipfile.ZipFile(zip_dest) as zf:
                zf.extractall(stage)
            entries = list(stage.iterdir())
            srcroot = entries[0] if len(entries) == 1 and entries[0].is_dir() else stage
            if target.exists():
                shutil.rmtree(target, ignore_errors=True)
            shutil.move(str(srcroot), str(target))
        zip_dest.unlink(missing_ok=True)
        _add_to_user_path_windows(str(target))
        if exe.is_file():
            return True
        console.error("doxygen.exe not found after extracting the portable archive.")
        return False
    except Exception as exc:
        console.error(f"Doxygen direct install failed: {exc}")
        return False


def _install_git_direct() -> bool:
    """Download and silently run the Git for Windows installer."""
    try:
        url = gh_latest_asset("git-for-windows/git", "*64-bit.exe")
        with tempfile.NamedTemporaryFile(suffix=".exe", delete=False) as f:
            dest = Path(f.name)
        download(url, dest)
        console.info("Installing Git silently ...")
        rc = subprocess.run(
            [str(dest), "/VERYSILENT", "/NORESTART", "/NOCANCEL", "/SP-",
             "/CLOSEAPPLICATIONS", "/RESTARTAPPLICATIONS",
             "/COMPONENTS=icons,ext\\reg\\shellhere,assoc,assoc_sh"],
            timeout=300,
        ).returncode
        dest.unlink(missing_ok=True)
        return rc == 0
    except Exception as exc:
        console.error(f"Git direct install failed: {exc}")
        return False


#: Maps winget package IDs to the command-line tool they provide.
WINGET_ID_TO_CMD: dict[str, str] = {
    "Kitware.CMake":              "cmake",
    "Ninja-build.Ninja":          "ninja",
    "Git.Git":                    "git",
    "DimitriVanHeesch.Doxygen":   "doxygen",
}

#: Maps winget IDs to direct-download installer functions.
_DIRECT_RECIPES: dict[str, Callable[[], bool]] = {
    "Kitware.CMake":             _install_cmake_direct,
    "Ninja-build.Ninja":         _install_ninja_direct,
    "Git.Git":                   _install_git_direct,
    "DimitriVanHeesch.Doxygen":  _install_doxygen_direct,
}


class DirectDownloadWindowsManager(IPackageManager):
    """Installs cmake, ninja, git and doxygen via direct downloads when winget is absent."""

    name = "direct-download"

    def available(self) -> bool:
        """Report that this manager is always usable."""
        return True

    def is_installed(self, pkg: str) -> bool:
        """Report whether *pkg*'s command already runs from PATH."""
        cmd = WINGET_ID_TO_CMD.get(pkg)
        path = shutil.which(cmd) if cmd else None
        return binary_works(path) if path else False

    def install(self, pkgs: list[str], dry_run: bool) -> bool:
        """Download and install each winget ID in *pkgs* that is not already on PATH."""
        refresh_windows_path()
        ok = True
        for pkg in pkgs:
            cmd = WINGET_ID_TO_CMD.get(pkg)
            if cmd and (w := shutil.which(cmd)) and binary_works(w):
                console.info(f"{cmd}: already on PATH, skipping.")
                continue
            recipe = _DIRECT_RECIPES.get(pkg)
            if recipe is None:
                console.warn(f"direct-download: no recipe for '{pkg}', skipping.")
                continue
            if dry_run:
                console.info(f"(dry-run) would download and install {pkg}.")
                continue
            ok = recipe() and ok
        return ok
