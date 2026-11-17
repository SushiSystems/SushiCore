# download_verifier.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Checks each download of a run against its pinned digest and names the unpinned ones.

The reasoning is in source/sushicore/provision/README.md, section "Verifying downloads".
"""

from __future__ import annotations

import logging
import typing
from pathlib import Path
from typing import Collection, Mapping

from sushicore.deps_fragment import Download
from sushicore.errors import ConfigError, DigestMismatchError

from .integrity import verify_sha256

_log = logging.getLogger(__name__)

#: The downloads each platform fetches for an entry a fragment declares, by manifest entry.
K_DOWNLOADS: dict[str, tuple[str, ...]] = {
    "windows": ("cmake", "ninja", "doxygen", "git", "intel-llvm", "adaptivecpp", "oneapi"),
    "linux": ("intel-llvm",),
}


@typing.final
class DownloadVerifier:
    """Verifies the downloads of one run and records the ones no manifest entry pins."""

    def __init__(self, digests: Mapping[str, str],
                 downloads: Mapping[str, Download] | None = None) -> None:
        """Hold the pinned digests and downloads of this run's platform.

        Args:
            digests: Manifest entry name to hex SHA-256; read on every :meth:`verify`.
            downloads: Manifest entry name to the download it pins; read on every :meth:`pinned`.
        """
        self._digests = digests
        self._downloads = downloads if downloads is not None else {}
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

    def pinned(self, name: str) -> Download:
        """Return the download the manifest entry *name* pins for this run's platform.

        Raises:
            ConfigError: No fragment of the run pins a download under *name*.
        """
        found = self._downloads.get(name)
        if found is None:
            raise ConfigError(
                f"No dependency fragment pins a download named '{name}' for this platform; "
                f"declare version, url and sha256 under [{name}] in a fragment.")
        return found

    def unverified(self) -> tuple[str, ...]:
        """Return the entries downloaded with no pinned digest, in the order first met."""
        return tuple(self._unverified)

    def _record_unverified(self, name: str, path: Path) -> None:
        """Record *name* as unpinned and warn about it the first time it is met."""
        if name in self._unverified:
            return
        self._unverified.append(name)
        _log.warning(
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


def pinned_download(name: str) -> Download:
    """Return the download the manifest entry *name* pins, through the bound verifier.

    Raises:
        ConfigError: No fragment of the run pins a download under *name*.
    """
    return _bound.pinned(name)


def unpinned_downloads(declared: Collection[str], digests: Mapping[str, str],
                       platform: str) -> list[str]:
    """Return the downloads a run on *platform* would fetch with no pinned digest.

    Args:
        declared: The names of the dependencies the fragments declare.
        digests: Manifest entry name to the digest pinned for *platform*.
    """
    fetched = [name for name in K_DOWNLOADS.get(platform, ()) if name in declared]
    return [name for name in fetched if not digests.get(name)]
