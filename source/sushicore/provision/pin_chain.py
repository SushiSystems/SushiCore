# pin_chain.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Walks the Sushi pins of a dependency chain and finds a library pinned at two versions."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from sushicore import deps_fragment
from sushicore.deps_fragment import SushiPin

from .closure import DEFAULT_FRAGMENT
from .sushi_sources import resolve


@dataclass(frozen=True)
class PinConflict:
    """One library two repositories of a chain pin at different versions."""

    name: str
    first_owner: str
    first_version: str
    second_owner: str
    second_version: str

    def message(self) -> str:
        """Return the line naming the library, both pinning repositories and both versions."""
        return (f"{self.name} is pinned at {self.first_version} by {self.first_owner} and at "
                f"{self.second_version} by {self.second_owner}; move every pin to one version "
                f"with `hub pin {self.name} <version>`.")


def conflicts(owner: str, root: Path, pins: Sequence[SushiPin]) -> list[PinConflict]:
    """Return every library the chain under *owner* pins at more than one version.

    The walk reads the fragment of each pinned library whose checkout resolves; a
    library with no checkout yet ends its branch.

    Args:
        owner: The name of the repository at *root*.
        root: Its checkout.
        pins: The pins of its own fragment.

    Raises:
        ValueError: A library's fragment is malformed.
    """
    seen: dict[str, tuple[str, str]] = {}
    found: list[PinConflict] = []
    walked: set[tuple[str, str]] = set()

    def visit(pinner: str, checkout: Path, own: Sequence[SushiPin]) -> None:
        """Record all of *pinner*'s pins, then walk each pinned library's own fragment."""
        agreed = []
        for pin in own:
            first = seen.setdefault(pin.name, (pinner, pin.version))
            if first[1] != pin.version:
                found.append(PinConflict(pin.name, first[0], first[1], pinner, pin.version))
            else:
                agreed.append(pin)
        for pin in agreed:
            if (pin.name, pin.version) in walked:
                continue
            walked.add((pin.name, pin.version))
            source = resolve(checkout, pin.name, pin.version)
            fragment = source.path / DEFAULT_FRAGMENT if source is not None else None
            if fragment is not None and fragment.is_file():
                visit(pin.name, source.path, deps_fragment.read(fragment).pins)

    visit(owner, root, pins)
    return found
