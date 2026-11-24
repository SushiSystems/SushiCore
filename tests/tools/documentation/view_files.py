# view_files.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Holds the design files the view tests and the generator tests share, and writes them under a root."""

from __future__ import annotations

from pathlib import Path, PurePosixPath

from sushicore.tools.documentation.design_status import Tree

K_TOPIC = """# Audio

**Status:** Open — phase A1 is building
**About:** The sound the engine makes.
**Modules:** modules/domain/audio

## Problem

None.

## Decision

None.

## Design

None.

## Phases

| Id | Phase | State |
| --- | --- | --- |
| A0 | The mixer | built |
| A1 | The spatializer | building |

## Open questions

None.
"""

K_OPEN_WORK = """# Spatializer

**Status:** Open — under way
**Implements:** AUDIO#A1

## Problem

None.
"""

K_CLOSED_WORK = K_OPEN_WORK.replace("Open — under way", "Shipped — 2026-10-01")

K_FILES = {
    "docs/design/README.md": "# Design\n\nThe topics.\n",
    "docs/design/AUDIO.md": K_TOPIC,
    "docs/agent/2026_10_20_SPATIALIZER/SPEC.md": K_OPEN_WORK,
    "docs/agent/2026_09_01_MIXER/SPEC.md": K_CLOSED_WORK.replace("AUDIO#A1", "AUDIO#A0"),
    "modules/domain/audio/README.md": "# Audio\n\nThe module.\n",
}


def tree_of(files: dict[str, str]) -> Tree:
    """Returns the folders, files and texts of a set of files, as the shell would read them."""
    folders = {"docs"}
    for name in files:
        folders.update(str(parent) for parent in PurePosixPath(name).parents if str(parent) != ".")
    return Tree(frozenset(folders), frozenset(files), files)


def write_files(folder: str, files: dict[str, str]) -> Path:
    """Writes the given files under a root and returns the root."""
    root = Path(folder) / "alpha"
    for name, text in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return root
