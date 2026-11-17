# compat.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The deprecated names ``sushicore.provision.packages`` exported before 0.16.0."""

from __future__ import annotations

import fnmatch
import json
import os
import shutil
import sys
import urllib.request
from typing import Any

from ...proc import Runner
from ...quiet_console import QuietConsole
from ..default_console import DEFAULT_CONSOLE
from ..deprecated_name import warn_deprecated
from ..process_run import run as run_command
from ..system import USER_AGENT, is_root
from .github_release import AssetNotFoundError

#: Seconds a release lookup waits for GitHub.
K_LOOKUP_TIMEOUT = 30

#: Where the controlling terminal is on a POSIX machine.
K_TTY = "/dev/tty"

#: What the sudo password prompt reads.
K_SUDO_PROMPT = "[sudo] password for %p: "


def _get_json(url: str) -> Any:
    """Return the JSON document *url* answers."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=K_LOOKUP_TIMEOUT) as response:
        return json.loads(response.read())


def gh_latest_asset(repo: str, asset_glob: str) -> str:
    """Return the download URL of the first asset of *repo*'s latest release matching *asset_glob*.

    Deprecated: pin the download in the dependency fragment, or use ``gh_tagged_asset``.

    Raises:
        AssetNotFoundError: No asset of the latest release matches.
    """
    warn_deprecated("gh_latest_asset", "gh_tagged_asset or a pinned fragment download")
    data = _get_json(f"https://api.github.com/repos/{repo}/releases/latest")
    for asset in data.get("assets", []):
        if fnmatch.fnmatch(asset["name"], asset_glob):
            return asset["browser_download_url"]
    raise AssetNotFoundError(f"No asset matching '{asset_glob}' in {repo} latest release.")


def gh_latest_release_asset(repo: str, asset_glob: str) -> tuple[str, str]:
    """Return ``(tag, url)`` of the newest asset of *repo* matching *asset_glob*, prereleases included.

    Deprecated: pin the download in the dependency fragment, or use ``gh_tagged_asset``.

    Raises:
        AssetNotFoundError: No asset of the last 20 releases matches.
    """
    warn_deprecated("gh_latest_release_asset", "gh_tagged_asset or a pinned fragment download")
    return _newest_asset(repo, asset_glob)


def gh_latest_asset_including_prerelease(repo: str, asset_glob: str) -> str:
    """Return the download URL of the newest asset of *repo* matching *asset_glob*, prereleases included.

    Deprecated: pin the download in the dependency fragment, or use ``gh_tagged_asset``.

    Raises:
        AssetNotFoundError: No asset of the last 20 releases matches.
    """
    warn_deprecated("gh_latest_asset_including_prerelease",
                    "gh_tagged_asset or a pinned fragment download")
    return _newest_asset(repo, asset_glob)[1]


def _newest_asset(repo: str, asset_glob: str) -> tuple[str, str]:
    """Return ``(tag, url)`` of the newest release asset matching *asset_glob*."""
    releases = _get_json(f"https://api.github.com/repos/{repo}/releases?per_page=20")
    for release in releases:
        for asset in release.get("assets", []):
            if fnmatch.fnmatch(asset["name"], asset_glob):
                return release.get("tag_name", ""), asset["browser_download_url"]
    raise AssetNotFoundError(f"No asset matching '{asset_glob}' in {repo} releases.")


def prime_sudo() -> None:
    """Prompt for the sudo password once, before any progress display starts.

    Deprecated: a command that needs sudo asks for it when it runs it.
    """
    warn_deprecated("prime_sudo", "the sudo prompt of the command that needs it")
    if os.name == "nt" or is_root() or shutil.which("sudo") is None:
        return
    console = DEFAULT_CONSOLE()
    tty = None
    if not (sys.stdin and sys.stdin.isatty()):
        try:
            tty = open(K_TTY, "r", encoding="utf-8")
        except OSError:
            console.warn(
                "No terminal available for a sudo password prompt. If dependency "
                "installation fails, run the install command directly in a terminal, "
                "or pre-authorize with `sudo -v`."
            )
            return
    console.warn("Administrator (sudo) access needed — enter your password below.")
    try:
        Runner(QuietConsole(), "sushicore").run(["sudo", "-p", K_SUDO_PROMPT, "-v"], None, stdin=tty)
    finally:
        if tty is not None:
            tty.close()


def run(cmd: list[str], dry_run: bool, *, check: bool = False) -> int:
    """Run *cmd*, streaming its output through the default console; return its exit code.

    Deprecated: use ``sushicore.provision.process_run.run`` with the console passed in.
    """
    warn_deprecated("packages.run", "sushicore.provision.process_run.run")
    return run_command(cmd, dry_run, console=DEFAULT_CONSOLE(), check=check)
