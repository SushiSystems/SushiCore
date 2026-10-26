# source_locator.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Finds the checkout of a Sushi library for the package walk."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from .. import sushi_sources
from .package_error import PackageError


class ISourceLocator(Protocol):
    """Finds a library's checkout."""

    def locate(self, root: Path, name: str, version: str, configured: str) -> Path:
        """Return the checkout of *name*; raise :class:`PackageError` when there is none."""


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
