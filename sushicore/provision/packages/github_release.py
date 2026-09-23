# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Resolves download URLs for GitHub release assets."""

from __future__ import annotations

import fnmatch
import json
import urllib.request

from ..system import USER_AGENT


def gh_latest_asset(repo: str, asset_glob: str) -> str:
    """Return the download URL for the first release asset matching *asset_glob*."""
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
    for asset in data.get("assets", []):
        if fnmatch.fnmatch(asset["name"], asset_glob):
            return asset["browser_download_url"]
    raise RuntimeError(f"No asset matching '{asset_glob}' in {repo} latest release.")


def gh_latest_asset_including_prerelease(repo: str, asset_glob: str) -> str:
    """Return the download URL for the newest matching asset, prereleases included."""
    return gh_latest_release_asset(repo, asset_glob)[1]


def gh_latest_release_asset(repo: str, asset_glob: str) -> tuple[str, str]:
    """Return ``(tag, url)`` for the newest matching asset, prereleases included."""
    url = f"https://api.github.com/repos/{repo}/releases?per_page=20"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        releases = json.loads(resp.read())
    for release in releases:
        for asset in release.get("assets", []):
            if fnmatch.fnmatch(asset["name"], asset_glob):
                return release.get("tag_name", ""), asset["browser_download_url"]
    raise RuntimeError(f"No asset matching '{asset_glob}' in {repo} releases.")


def gh_tagged_asset(repo: str, tag: str, asset_glob: str) -> str:
    """Return the download URL for an asset of a specific release *tag*."""
    url = f"https://api.github.com/repos/{repo}/releases/tags/{tag}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
    for asset in data.get("assets", []):
        if fnmatch.fnmatch(asset["name"], asset_glob):
            return asset["browser_download_url"]
    raise RuntimeError(f"No asset matching '{asset_glob}' in {repo} {tag}.")
