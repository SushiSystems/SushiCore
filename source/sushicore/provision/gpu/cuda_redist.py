# cuda_redist.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Reads NVIDIA's CUDA redistributable index: which releases exist and the archives of each.

NVIDIA publishes one ``redistrib_<version>.json`` per release beside the archives it names, each
with a SHA-256. Nothing here names a CUDA version; every release comes from the index itself.
"""

from __future__ import annotations

import json
import re
import typing
import urllib.request

from ..system import USER_AGENT
from .cuda_release import RedistArchive, RedistRelease, Version, format_version, parse_version
from .toolkit_vendor import ToolkitSourceError

#: The root NVIDIA serves the redistributable index and archives from.
K_REDIST_ROOT = "https://developer.download.nvidia.com/compute/cuda/redist/"

K_MANIFEST_NAME = re.compile(r"redistrib_(\d+(?:\.\d+)+)\.json")

class RedistError(ToolkitSourceError):
    """The redistributable index could not be read or did not parse."""


@typing.final
class RedistIndex:
    """NVIDIA's redistributable index, read through an injected text fetcher.

    Args:
        fetch_text: Returns the body at a URL; raises ``OSError`` when it cannot.
        root: The index root, ending in ``/``.
    """

    def __init__(self, fetch_text: typing.Callable[[str], str] | None = None,
                 root: str = K_REDIST_ROOT) -> None:
        """Store the fetcher and the index root."""
        self._fetch_text = fetch_text or _fetch_text
        self._root = root

    def versions(self) -> list[Version]:
        """Return every published release, newest first.

        Raises:
            RedistError: The index could not be read.
        """
        listing = self._read(self._root)
        found = {parse_version(m.group(1)) for m in K_MANIFEST_NAME.finditer(listing)}
        return sorted(found, reverse=True)

    def release(self, version: Version, platform_key: str) -> RedistRelease:
        """Return the archives *version* publishes for *platform_key*, such as ``linux-x86_64``.

        Raises:
            RedistError: The manifest could not be read or is not the expected JSON.
        """
        body = self._read(f"{self._root}redistrib_{format_version(version)}.json")
        try:
            manifest = json.loads(body)
            archives = {
                name: RedistArchive(self._root + entry[platform_key]["relative_path"],
                                    entry[platform_key]["sha256"])
                for name, entry in manifest.items()
                if isinstance(entry, dict) and platform_key in entry
            }
        except (ValueError, KeyError, TypeError) as error:
            raise RedistError(f"CUDA {format_version(version)} manifest is malformed: "
                              f"{error}") from error
        return RedistRelease(version, archives)

    def _read(self, url: str) -> str:
        """Fetch *url*, turning a transport failure into :class:`RedistError`."""
        try:
            return self._fetch_text(url)
        except OSError as error:
            raise RedistError(f"{url} could not be read: {error}") from error


def _fetch_text(url: str) -> str:
    """Return the UTF-8 body served at *url*."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8")
