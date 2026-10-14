# rocm_tarball_index.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Reads AMD's ROCm SDK tarball listing: every release, for every family of cards.

AMD names each tarball ``therock-dist-<platform>-<family>-<version>.tar.gz``. Nothing here
names a ROCm version or a family; both come from the listing itself.
"""

from __future__ import annotations

import re
import typing
import urllib.request

from ..system import USER_AGENT
from .rocm_package import RocmPackage
from .toolkit_vendor import ToolkitSourceError

#: The page AMD serves the tarballs from.
K_TARBALL_ROOT = "https://repo.amd.com/rocm/tarball/"

K_TARBALL_NAME = re.compile(
    r"therock-dist-(?P<platform>[a-z]+)-(?P<family>gfx[0-9A-Za-z]+(?:-[a-z]+)?)-"
    r"(?P<version>\d+(?:\.\d+)+)\.tar\.gz")


class RocmIndexError(ToolkitSourceError):
    """The tarball listing could not be read."""


@typing.final
class RocmTarballIndex:
    """AMD's tarball listing, read through an injected text fetcher.

    Args:
        fetch_text: Returns the body at a URL; raises ``OSError`` when it cannot.
        root: The listing's URL, ending in ``/``.
    """

    def __init__(self, fetch_text: typing.Callable[[str], str] | None = None,
                 root: str = K_TARBALL_ROOT) -> None:
        """Store the fetcher and the listing's URL."""
        self._fetch_text = fetch_text or _fetch_text
        self._root = root

    def packages(self, platform: str) -> list[RocmPackage]:
        """Return every tarball for *platform*, such as ``linux``, newest release first.

        Raises:
            RocmIndexError: The listing could not be read.
        """
        try:
            listing = self._fetch_text(self._root)
        except OSError as error:
            raise RocmIndexError(f"{self._root} could not be read: {error}") from error
        found = {
            RocmPackage(tuple(int(p) for p in m.group("version").split(".")),
                        m.group("family"), self._root + m.group(0))
            for m in K_TARBALL_NAME.finditer(listing) if m.group("platform") == platform
        }
        return sorted(found, key=lambda p: (p.version, p.family), reverse=True)


def _fetch_text(url: str) -> str:
    """Return the UTF-8 body served at *url*."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8")
