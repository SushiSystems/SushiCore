# direct_download.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Installs cmake, ninja, git and doxygen on Windows via direct GitHub downloads."""

from __future__ import annotations

import logging
import os
import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path
from typing import Any, Callable, MutableMapping

from sushicore.errors import ConfigError, DigestMismatchError
from sushicore.proc import CommandRunner

from ..default_console import console_or_default
from .. import home
from sushicore.deps_fragment import Download

from ..download_verifier import pinned_download, verify_download
from ..probe import binary_works
from ..process_run import provision_runner
from ..system import USER_AGENT
from .base import IPackageManager, refresh_windows_path

_log = logging.getLogger(__name__)


def tools_dir() -> Path:
    """Return the directory where portable tools (cmake, ninja) install."""
    return home.tools_dir()


def download(url: str, dest: Path, console: Any = None) -> None:
    """Fetch *url* into *dest*, announcing it on *console* and streaming the response in chunks."""
    console = console_or_default(console, "download")
    console.info(f"Downloading {dest.name} ...")
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=300) as resp, open(dest, "wb") as fh:
        while chunk := resp.read(1 << 16):
            fh.write(chunk)


def downloader(console: Any = None) -> Callable[[str, Path], None]:
    """Return the download transport that announces each fetch on *console*."""
    console = console_or_default(console, "downloader")
    return lambda url, dest: download(url, dest, console)


def _add_to_user_path_windows(directory: str, winreg: Any = None,
                              environ: MutableMapping[str, str] | None = None) -> bool:
    """Append *directory* to this process's PATH and the user's PATH registry key.

    Args:
        winreg: The ``winreg`` module, or an object with its calls; the real module when ``None``.
        environ: The environment whose PATH is extended; the process's when ``None``.

    Returns:
        True when the registry holds *directory*, False when only this process does.
    """
    env = os.environ if environ is None else environ
    env["PATH"] = env.get("PATH", "") + os.pathsep + directory
    try:
        if winreg is None:
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
    except OSError as error:
        _log.warning(
            "%s was not added to the user's PATH in the registry (%s: %s); "
            "only this process finds it",
            directory,
            type(error).__name__,
            error,
        )
        return False
    return True


def _put_on_user_path(directory: str, console: Any,
                      add_to_path: Callable[[str], bool] | None = None) -> None:
    """Add *directory* to the user's PATH and warn on *console* when only this run has it.

    Args:
        console: The console the warning is printed through.
        add_to_path: Writes the directory to the user's PATH and answers whether the registry
            holds it; the Windows registry writer when ``None``.
    """
    if not (add_to_path or _add_to_user_path_windows)(directory):
        console.warn(
            f"{directory} is on PATH for this run only; add it to the user PATH by hand."
        )


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


def _replace_folder_with_archive(archive: Path, target: Path, console: Any) -> bool:
    """Replace *target* with the contents of the zip *archive*, unless *target* is protected.

    Args:
        console: The console a refusal is printed through.

    Returns:
        False, with the folder untouched, when *target* is not a safe dependency root.
    """
    with tempfile.TemporaryDirectory() as staging:
        stage = Path(staging)
        with zipfile.ZipFile(archive) as zf:
            zf.extractall(stage)
        entries = list(stage.iterdir())
        srcroot = entries[0] if len(entries) == 1 and entries[0].is_dir() else stage
        if target.exists():
            if not home.is_removable_root(target):
                console.error(f"Refusing to remove {target}: not a safe dependency root.")
                return False
            shutil.rmtree(target, ignore_errors=True)
        shutil.move(str(srcroot), str(target))
    return True


def _install_cmake_direct(*, console: Any, pin: Callable[[str], Download] | None = None,
                          fetch: Callable[[str, Path], None] | None = None,
                          cmake_on_system: Callable[[], str] | None = None,
                          on_path: Callable[[str], None] | None = None) -> bool:
    """Extract the portable CMake zip into the tools dir and add it to PATH.

    Args:
        console: The console the install prints through.
        pin: Maps an entry name to its pinned download; the bound verifier's when ``None``.
        fetch: Downloads a URL into a file; the download transport.
        cmake_on_system: Finds a cmake already installed, or returns an empty string.
        on_path: Puts a directory on the user's PATH.
    """
    if (cmake_on_system or _cmake_on_system)():
        console.info("cmake: already present, skipping.")
        return True
    try:
        pinned = (pin or pinned_download)("cmake")
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as f:
            zip_dest = Path(f.name)
        (fetch or downloader(console))(pinned.url, zip_dest)
        verify_download("cmake", zip_dest)
        target = tools_dir() / "cmake"
        console.info(f"Extracting CMake to {target} ...")
        if not _replace_folder_with_archive(zip_dest, target, console):
            return False
        zip_dest.unlink(missing_ok=True)
        (on_path or (lambda directory: _put_on_user_path(directory, console)))(
            str(_cmake_portable_bin()))
        if (_cmake_portable_bin() / "cmake.exe").is_file():
            return True
        console.error("CMake not found after extracting the portable archive.")
        return False
    except (DigestMismatchError, ConfigError):
        raise
    except Exception as exc:
        console.error(f"CMake direct install failed: {exc}")
        return False


def _install_ninja_direct(*, console: Any, pin: Callable[[str], Download] | None = None,
                          fetch: Callable[[str, Path], None] | None = None,
                          on_path: Callable[[str], None] | None = None) -> bool:
    """Extract the ninja.exe archive into the tools dir and add it to PATH.

    Args:
        console: The console the install prints through.
        pin: Maps an entry name to its pinned download; the bound verifier's when ``None``.
        fetch: Downloads a URL into a file; the download transport.
        on_path: Puts a directory on the user's PATH.
    """
    try:
        pinned = (pin or pinned_download)("ninja")
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as f:
            dest = Path(f.name)
        (fetch or downloader(console))(pinned.url, dest)
        verify_download("ninja", dest)
        tools = tools_dir()
        tools.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(dest) as zf:
            zf.extract("ninja.exe", tools)
        dest.unlink(missing_ok=True)
        (on_path or (lambda directory: _put_on_user_path(directory, console)))(str(tools))
        return (tools / "ninja.exe").is_file()
    except (DigestMismatchError, ConfigError):
        raise
    except Exception as exc:
        console.error(f"Ninja direct install failed: {exc}")
        return False


def _install_doxygen_direct(*, console: Any, pin: Callable[[str], Download] | None = None,
                            fetch: Callable[[str, Path], None] | None = None,
                            on_path: Callable[[str], None] | None = None) -> bool:
    """Extract the portable Doxygen zip into the tools dir and add it to PATH.

    Args:
        console: The console the install prints through.
        pin: Maps an entry name to its pinned download; the bound verifier's when ``None``.
        fetch: Downloads a URL into a file; the download transport.
        on_path: Puts a directory on the user's PATH.
    """
    target = tools_dir() / "doxygen"
    exe = target / "doxygen.exe"
    if exe.is_file():
        console.info("doxygen: already present in deps/tools, skipping.")
        return True
    try:
        pinned = (pin or pinned_download)("doxygen")
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as f:
            zip_dest = Path(f.name)
        (fetch or downloader(console))(pinned.url, zip_dest)
        verify_download("doxygen", zip_dest)
        console.info(f"Extracting Doxygen to {target} ...")
        if not _replace_folder_with_archive(zip_dest, target, console):
            return False
        zip_dest.unlink(missing_ok=True)
        (on_path or (lambda directory: _put_on_user_path(directory, console)))(str(target))
        if exe.is_file():
            return True
        console.error("doxygen.exe not found after extracting the portable archive.")
        return False
    except (DigestMismatchError, ConfigError):
        raise
    except Exception as exc:
        console.error(f"Doxygen direct install failed: {exc}")
        return False


def _install_git_direct(*, console: Any, pin: Callable[[str], Download] | None = None,
                        fetch: Callable[[str, Path], None] | None = None,
                        runner: CommandRunner | None = None) -> bool:
    """Download and silently run the Git for Windows installer.

    Args:
        console: The console the install prints through.
        pin: Maps an entry name to its pinned download; the bound verifier's when ``None``.
        fetch: Downloads a URL into a file; the download transport.
        runner: Runs the installer command, stopped after 300 seconds; the provision runner
            on *console* when ``None``.
    """
    try:
        pinned = (pin or pinned_download)("git")
        with tempfile.NamedTemporaryFile(suffix=".exe", delete=False) as f:
            dest = Path(f.name)
        (fetch or downloader(console))(pinned.url, dest)
        verify_download("git", dest)
        console.info("Installing Git silently ...")
        rc, _stdout, _stderr = (runner or provision_runner(console)).capture(
            [str(dest), "/VERYSILENT", "/NORESTART", "/NOCANCEL", "/SP-",
             "/CLOSEAPPLICATIONS", "/RESTARTAPPLICATIONS",
             "/COMPONENTS=icons,ext\\reg\\shellhere,assoc,assoc_sh"],
            timeout=300,
        )
        dest.unlink(missing_ok=True)
        return rc == 0
    except (DigestMismatchError, ConfigError):
        raise
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
_DIRECT_RECIPES: dict[str, Callable[..., bool]] = {
    "Kitware.CMake":             _install_cmake_direct,
    "Ninja-build.Ninja":         _install_ninja_direct,
    "Git.Git":                   _install_git_direct,
    "DimitriVanHeesch.Doxygen":  _install_doxygen_direct,
}


class DirectDownloadWindowsManager(IPackageManager):
    """Installs cmake, ninja, git and doxygen via direct downloads when winget is absent."""

    name = "direct-download"

    def __init__(self, runner: CommandRunner | None = None, *, console: Any = None) -> None:
        """Bind the console and the runner that probes whether a tool runs.

        Args:
            runner: Probes whether a tool runs; the provision runner on *console* when ``None``.
            console: The console the manager and its recipes print through.
        """
        console = console_or_default(console, "DirectDownloadWindowsManager")
        super().__init__(console=console)
        self._runner = runner if runner is not None else provision_runner(console)

    def available(self) -> bool:
        """Report that this manager is always usable."""
        return True

    def is_installed(self, pkg: str) -> bool:
        """Report whether *pkg*'s command already runs from PATH."""
        cmd = WINGET_ID_TO_CMD.get(pkg)
        path = shutil.which(cmd) if cmd else None
        return binary_works(path, self._runner) if path else False

    def install(self, pkgs: list[str], dry_run: bool) -> bool:
        """Download and install each winget ID in *pkgs* that is not already on PATH."""
        refresh_windows_path()
        ok = True
        for pkg in pkgs:
            cmd = WINGET_ID_TO_CMD.get(pkg)
            if cmd and (w := shutil.which(cmd)) and binary_works(w, self._runner):
                self._console.info(f"{cmd}: already on PATH, skipping.")
                continue
            recipe = _DIRECT_RECIPES.get(pkg)
            if recipe is None:
                self._console.warn(f"direct-download: no recipe for '{pkg}', skipping.")
                continue
            if dry_run:
                self._console.info(f"(dry-run) would download and install {pkg}.")
                continue
            ok = recipe(console=self._console) and ok
        return ok
