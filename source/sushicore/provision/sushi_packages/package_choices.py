# package_choices.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Records which package each library of a closure was chosen at, and by whom."""

from __future__ import annotations

from .package_error import PackageConflictError


class PackageChoices:
    """One digest per library: a second, different digest is a conflict."""

    def __init__(self) -> None:
        """Start with nothing chosen."""
        self._chosen: dict[str, tuple[str, str]] = {}

    def add(self, name: str, digest: str, owner: str) -> None:
        """Record that *owner* chose *digest* for *name*.

        Raises:
            PackageConflictError: *name* was chosen at another digest; the message names both
                digests and both choosers.
        """
        first = self._chosen.setdefault(name, (digest, owner))
        if first[0] != digest:
            raise PackageConflictError(
                f"{name} would be used at two keys: {first[0][:12]} chosen by {first[1]} and "
                f"{digest[:12]} chosen by {owner}; a closure links one package per library.")
