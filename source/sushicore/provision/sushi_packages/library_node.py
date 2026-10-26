# library_node.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""One library of a consumer chain, as the walk found it."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class LibraryNode:
    """A library's name, checkout, CLI, source exclusions and the libraries it depends on."""

    name: str
    checkout: Path
    #: The command of the library's own CLI, empty when its fragment names none.
    cli: str
    package_exclude: tuple[str, ...]
    depends_on: tuple[str, ...]
