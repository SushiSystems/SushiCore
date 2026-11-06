# source_locator.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Finds the checkout of a Sushi library for the package walk."""

from __future__ import annotations

from pathlib import Path
from typing import Mapping, Protocol

from .. import sushi_sources
from .package_error import PackageError


class ISourceLocator(Protocol):
    """Finds a library's checkout."""

    def locate(self, root: Path, name: str, version: str, configured: str) -> Path:
        """Return the checkout of *name*; raise :class:`PackageError` when there is none."""


class MemoryLocator:
    """Answers the checkout set for a library and searches nothing.

    Args:
        checkouts: The checkout of each library, by name.

    Attributes:
        asked: The ``(name, version)`` of every call, in order.
    """

    def __init__(self, checkouts: Mapping[str, Path]) -> None:
        """Keep *checkouts*; nothing has been asked yet."""
        self._checkouts = dict(checkouts)
        self.asked: list[tuple[str, str]] = []

    def locate(self, root: Path, name: str, version: str, configured: str) -> Path:
        """Record the name and the version, and return the checkout of *name*.

        Raises:
            PackageError: No checkout was set for *name*.
        """
        self.asked.append((name, version))
        if name not in self._checkouts:
            raise PackageError(f"{name} has no checkout.")
        return self._checkouts[name]


class SushiSourceLocator:
    """Finds a checkout through ``<NAME>_DIR``, the sibling and the fetched copy."""

    def locate(self, root: Path, name: str, version: str, configured: str) -> Path:
        """Return the checkout of *name* for the consumer at *root*.

        Args:
            root: The consumer's checkout.
            name: The library's lower-case name.
            version: The pinned tag, or '' when nothing pins it.
            configured: ``<NAME>_DIR`` from the config, or ''.

        Raises:
            PackageError: No checkout exists; the message names ``<NAME>_DIR``.
        """
        found = sushi_sources.resolve(root, name, version, configured)
        if found is None:
            raise PackageError(
                f"{name} has no checkout: set {sushi_sources.directory_variable(name)}, place it "
                f"beside {root.name}, or run `setup` to fetch the pinned tag.")
        return found.path
