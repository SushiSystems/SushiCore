# cuda_release.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""One CUDA release as NVIDIA's redistributable index describes it: its version and archives."""

from __future__ import annotations

import dataclasses
import typing

Version = tuple[int, ...]


@typing.final
@dataclasses.dataclass(frozen=True, slots=True)
class RedistArchive:
    """One component archive of a release.

    Args:
        url: Where the archive is served.
        sha256: The digest NVIDIA publishes for it.
    """

    url: str
    sha256: str

    @property
    def file_name(self) -> str:
        """Return the archive's file name."""
        return self.url.rsplit("/", 1)[-1]


@typing.final
@dataclasses.dataclass(frozen=True, slots=True)
class RedistRelease:
    """The archives one CUDA release publishes for one platform.

    Args:
        version: The release, such as ``(13, 1, 2)``.
        archives: Component name, such as ``cuda_nvcc``, to its archive.
    """

    version: Version
    archives: dict[str, RedistArchive]

    @property
    def label(self) -> str:
        """Return the release as text, such as ``13.1.2``."""
        return format_version(self.version)


def parse_version(text: str) -> Version:
    """Return ``"13.1.2"`` as ``(13, 1, 2)``.

    Raises:
        ValueError: *text* is not dot-separated digits.
    """
    return tuple(int(part) for part in text.strip().split("."))


def format_version(version: Version) -> str:
    """Return ``(13, 1, 2)`` as ``"13.1.2"``."""
    return ".".join(str(part) for part in version)
