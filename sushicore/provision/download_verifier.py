# download_verifier.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Checks each download of a run against its pinned digest and names the unpinned ones.

The reasoning is in sushicore/provision/README.md, section "Verifying downloads".
"""

from __future__ import annotations

import logging
import typing
from pathlib import Path
from typing import Collection, Mapping

from sushicore.errors import DigestMismatchError

from .integrity import verify_sha256

K_LOGGER = logging.getLogger("sushicore.provision")

#: The downloads each platform fetches whatever the fragments declare, by manifest entry.
K_TOOL_DOWNLOADS: dict[str, tuple[str, ...]] = {
    "windows": ("cmake", "ninja", "doxygen", "git"),
}

#: The downloads each platform fetches only for a dependency a fragment declares.
K_DECLARED_DOWNLOADS: dict[str, tuple[str, ...]] = {
    "windows": ("intel-llvm", "adaptivecpp", "oneapi", "cuda"),
    "linux": ("intel-llvm",),
}


@typing.final
class DownloadVerifier:
    """Verifies the downloads of one run and records the ones no manifest entry pins."""

    def __init__(self, digests: Mapping[str, str]) -> None:
        """Hold the pinned digests of this run's platform.

        Args:
            digests: Manifest entry name to hex SHA-256; read on every :meth:`verify`.
        """
        self._digests = digests
        self._unverified: list[str] = []

    def verify(self, name: str, path: Path) -> None:
        """Check the file downloaded for the manifest entry *name*, or record it as unpinned.

        Raises:
            DigestMismatchError: The entry pins a digest the file does not have; the
                file is deleted first, so nothing can open or run it.
        """
        expected = self._digests.get(name, "")
        if not expected:
            self._record_unverified(name, path)
            return
        try:
            verify_sha256(path, expected)
        except DigestMismatchError:
            path.unlink(missing_ok=True)
            raise

    def unverified(self) -> tuple[str, ...]:
        """Return the entries downloaded with no pinned digest, in the order first met."""
        return tuple(self._unverified)

    def _record_unverified(self, name: str, path: Path) -> None:
        """Record *name* as unpinned and warn about it the first time it is met."""
        if name in self._unverified:
            return
        self._unverified.append(name)
        K_LOGGER.warning(
            "%s was downloaded to %s with no sha256 pinned in its manifest entry; "
            "the file is used unverified",
            name,
            path,
        )


_bound = DownloadVerifier({})


def bind_verifier(verifier: DownloadVerifier | None) -> None:
    """Make *verifier* the one the download sites call;``None`` binds one that pins nothing."""
    global _bound
    _bound = verifier if verifier is not None else DownloadVerifier({})


def verify_download(name: str, path: Path) -> None:
    """Verify the file downloaded for the manifest entry *name* through the bound verifier.

    Raises:
        DigestMismatchError: The entry pins a digest the file does not have.
    """
    _bound.verify(name, path)


def unpinned_downloads(declared: Collection[str], digests: Mapping[str, str],
                       platform: str) -> list[str]:
    """Return the downloads a run on *platform* would fetch with no pinned digest.

    Args:
        declared: The names of the dependencies the fragments declare.
        digests: Manifest entry name to the digest pinned for *platform*.
    """
    fetched = [*K_TOOL_DOWNLOADS.get(platform, ()),
               *(name for name in K_DECLARED_DOWNLOADS.get(platform, ()) if name in declared)]
    return [name for name in fetched if not digests.get(name)]
