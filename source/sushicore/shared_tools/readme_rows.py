# readme_rows.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Merges the rows of the shared tools into the table of a repository's `tools/README.md`."""

from __future__ import annotations

import re
from collections.abc import Collection

K_ROW = re.compile(r"^\| `([^`]+)` \|")
K_HEADER = "| Path | Checks | Takes |\n| --- | --- | --- |"
K_TOOLS_PREFIX = "tools/"


def merge_readme(current: str | None, source: str, shared: Collection[str]) -> str:
    """Returns the README text holding the shared rows of *source* beside the rows *current* owns.

    A row of *current* whose path a shared row names is replaced in place; a shared row it lacks
    follows its last table row; every other line stays. A *current* without a table gets one.

    Args:
        current: The README the repository holds, or None when it has none.
        source: The README of the SushiCore tag.
        shared: The repository paths, such as `tools/check_all.py`, the sync copies.
    """
    rows = _shared_rows(source, shared)
    lines = (current or "# tools\n").rstrip("\n").split("\n")
    placed: set[str] = set()
    last = -1
    for index, line in enumerate(lines):
        found = K_ROW.match(line)
        if found is None:
            continue
        last = index
        if found.group(1) in rows:
            lines[index] = rows[found.group(1)]
            placed.add(found.group(1))
    missing = [row for path, row in rows.items() if path not in placed]
    if missing and last < 0:
        lines += ["", *K_HEADER.split("\n")]
        last = len(lines) - 1
    lines[last + 1 : last + 1] = missing
    return "\n".join(lines) + "\n"


def _shared_rows(source: str, shared: Collection[str]) -> dict[str, str]:
    """Returns the table rows of *source* that describe a shared path, keyed by that path."""
    rows = {}
    for line in source.split("\n"):
        found = K_ROW.match(line)
        if found is not None and _is_shared(found.group(1), shared):
            rows[found.group(1)] = line
    return rows


def _is_shared(path: str, shared: Collection[str]) -> bool:
    """Returns whether a row path names a shared file, or a folder holding one."""
    full = K_TOOLS_PREFIX + path
    if full.endswith("/"):
        return any(name.startswith(full) for name in shared)
    return full in shared
