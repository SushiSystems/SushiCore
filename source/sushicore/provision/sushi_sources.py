# sushi_sources.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Finds the checkout of a Sushi library: its directory variable, the sibling, then the fetched copy."""

from __future__ import annotations

import enum
import os
from dataclasses import dataclass
from pathlib import Path

from . import home


class SourceKind(str, enum.Enum):
    """Where a Sushi library's checkout was found."""

    #: ``<NAME>_DIR``, from the config or the environment.
    DIRECTORY = "directory"
    #: The sibling checkout ``../<name>``.
    SIBLING = "sibling"
    #: The copy ``setup`` cloned under ``<home>/sources/<name>/<version>/``.
    FETCHED = "fetched"


@dataclass(frozen=True)
class ResolvedSource:
    """The checkout of one Sushi library and where it was found."""

    path: Path
    kind: SourceKind


def directory_variable(name: str) -> str:
    """Return the variable naming *name*'s checkout, such as ``SUSHILOG_DIR``."""
    return f"{name.upper()}_DIR"


def fetched_dir(name: str, version: str) -> Path:
    """Return ``<home>/sources/<name>/<version>``, where ``setup`` clones *name* at *version*."""
    return home.sources_dir() / name / version


def sibling_dir(root: Path, name: str) -> Path:
    """Return ``<root>/../<name>``, the checkout a workspace lays out beside *root*."""
    return (root / ".." / name).resolve()


def resolve(root: Path, name: str, version: str = "", configured: str = "") -> ResolvedSource | None:
    """Return the first checkout of *name* that exists, or None when there is none.

    Args:
        root: The checkout of the module that links *name*.
        name: The library's lower-case name, such as ``sushilog``.
        version: The pinned release tag; without one the fetched copy is not looked for.
        configured: ``<NAME>_DIR`` from the config; the environment is read when it is empty.
    """
    explicit = configured or os.environ.get(directory_variable(name), "")
    candidates: list[tuple[Path, SourceKind]] = []
    if explicit:
        expanded = os.path.expandvars(os.path.expanduser(explicit))
        candidates.append((Path(expanded).resolve(), SourceKind.DIRECTORY))
    candidates.append((sibling_dir(root, name), SourceKind.SIBLING))
    if version:
        candidates.append((fetched_dir(name, version), SourceKind.FETCHED))
    for path, kind in candidates:
        if path.is_dir():
            return ResolvedSource(path, kind)
    return None
