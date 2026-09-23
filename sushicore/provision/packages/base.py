# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""The package-manager contract, its process helpers, and GPU stack dispatch."""

from __future__ import annotations

import fnmatch
import json
import os
import shutil
import subprocess
import sys
import typing
import urllib.request
from abc import ABC, abstractmethod

from .._output import console
from ..gpu.registry import DEFAULT_REGISTRY
from ..system import is_root

if typing.TYPE_CHECKING:
    from ..config import ProvisionConfig


def _run(cmd: list[str], dry_run: bool, *, check: bool = False) -> int:
    """Run *cmd*, streaming its output through the console; return its exit code."""
    console.command(subprocess.list2cmdline(cmd))
    if dry_run:
        console.info("(dry-run) not executed")
        return 0
    process = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding="utf-8", errors="replace",
    )
    if process.stdout:
        for line in iter(process.stdout.readline, ""):
            console.console.print(line.rstrip("\n"), markup=False, highlight=False)
    process.wait()
    if check and process.returncode != 0:
        console.error(f"Command failed ({process.returncode}).")
    return process.returncode


def prime_sudo() -> None:
    """Prompt for the sudo password once, before any progress display starts.

    No-op when already root, on Windows, or when sudo is absent.
    """
    if os.name == "nt" or is_root() or shutil.which("sudo") is None:
        return

    tty = None
    if not (sys.stdin and sys.stdin.isatty()):
        try:
            tty = open("/dev/tty", "r")
        except OSError:
            console.warn(
                "No terminal available for a sudo password prompt. If dependency "
                "installation fails, run the install command directly in a terminal, "
                "or pre-authorize with `sudo -v`."
            )
            return

    console.warn("Administrator (sudo) access needed — enter your password below.")
    try:
        subprocess.run(["sudo", "-p", "[sudo] password for %p: ", "-v"], stdin=tty)
    except OSError as exc:
        console.warn(f"Could not prime sudo credentials: {exc}")
    finally:
        if tty is not None:
            tty.close()


def refresh_windows_path() -> None:
    """Reload PATH from the registry into this process (Windows only, else no-op)."""
    if os.name != "nt":
        return
    try:
        import winreg
        parts: list[str] = []
        for root, sub in (
            (winreg.HKEY_LOCAL_MACHINE,
             r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"),
            (winreg.HKEY_CURRENT_USER, r"Environment"),
        ):
            try:
                key = winreg.OpenKey(root, sub)
                try:
                    val, _ = winreg.QueryValueEx(key, "Path")
                    parts.append(os.path.expandvars(str(val)))
                finally:
                    winreg.CloseKey(key)
            except FileNotFoundError:
                pass
        parts.append(os.environ.get("PATH", ""))  # keep this process's own additions
        seen: set[str] = set()
        out: list[str] = []
        for entry in os.pathsep.join(parts).split(os.pathsep):
            key_l = entry.lower()
            if entry and key_l not in seen:
                seen.add(key_l)
                out.append(entry)
        os.environ["PATH"] = os.pathsep.join(out)
    except Exception:
        pass


def install_gpu_stack(cfg: "ProvisionConfig", vendor: str, dry_run: bool) -> bool:
    """Provision the compute SDK for the detected GPU *vendor* through its backend spec.

    Looks *vendor* up in the GPU backend registry and delegates to its locator's
    ``provision``. Always best-effort: a failure here never raises.
    """
    spec = DEFAULT_REGISTRY.for_probe_vendor(vendor)
    if spec is None:
        console.info("No discrete GPU detected; using the CPU (SPIR/OpenCL) path only.")
        return True
    return spec.locator.provision(cfg, dry_run)


def _gh_latest_asset(repo: str, asset_glob: str) -> str:
    """Return the download URL for the first release asset matching *asset_glob*."""
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    req = urllib.request.Request(url, headers={"User-Agent": "sushiruntime-installer"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
    for asset in data.get("assets", []):
        if fnmatch.fnmatch(asset["name"], asset_glob):
            return asset["browser_download_url"]
    raise RuntimeError(f"No asset matching '{asset_glob}' in {repo} latest release.")


def _gh_latest_asset_including_prerelease(repo: str, asset_glob: str) -> str:
    """Return the download URL for the newest matching asset, prereleases included."""
    return _gh_latest_release_asset(repo, asset_glob)[1]


def _gh_latest_release_asset(repo: str, asset_glob: str) -> tuple[str, str]:
    """Return ``(tag, url)`` for the newest matching asset, prereleases included.

    :param repo: ``owner/name`` of the GitHub repository.
    :param asset_glob: Shell-style pattern the asset filename must match.
    :return: The release tag and the asset's download URL.
    :raises RuntimeError: If no release in the recent window carries a match.
    """
    url = f"https://api.github.com/repos/{repo}/releases?per_page=20"
    req = urllib.request.Request(url, headers={"User-Agent": "sushiruntime-installer"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        releases = json.loads(resp.read())
    for release in releases:
        for asset in release.get("assets", []):
            if fnmatch.fnmatch(asset["name"], asset_glob):
                return release.get("tag_name", ""), asset["browser_download_url"]
    raise RuntimeError(f"No asset matching '{asset_glob}' in {repo} releases.")


def _gh_tagged_asset(repo: str, tag: str, asset_glob: str) -> str:
    """Return the download URL for an asset of a specific release *tag*."""
    url = f"https://api.github.com/repos/{repo}/releases/tags/{tag}"
    req = urllib.request.Request(url, headers={"User-Agent": "sushiruntime-installer"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
    for asset in data.get("assets", []):
        if fnmatch.fnmatch(asset["name"], asset_glob):
            return asset["browser_download_url"]
    raise RuntimeError(f"No asset matching '{asset_glob}' in {repo} {tag}.")


class IPackageManager(ABC):
    """Installs packages of one kind and reports availability."""

    name: str = "pkg"

    @abstractmethod
    def available(self) -> bool:
        """Is the underlying tool present on this machine?"""

    @abstractmethod
    def is_installed(self, pkg: str) -> bool:
        """Best-effort check whether *pkg* is already installed."""

    @abstractmethod
    def install(self, pkgs: list[str], dry_run: bool) -> bool:
        """Install the given packages. Return True on success."""

    def remove(self, pkgs: list[str], dry_run: bool) -> bool:
        """Remove the given packages. Return True on success (best-effort)."""
        console.warn(f"{self.name}: remove not implemented, skipping.")
        return True
