# closure_memory.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""A module locator that answers from a table and looks at no folder."""

from __future__ import annotations

from pathlib import Path
from typing import Mapping


class TableLocator:
    """Finds the checkout of a module in a table, as a :data:`closure.Locate` does.

    Args:
        checkouts: The checkout of each module that has one, by module name.
    """

    def __init__(self, checkouts: Mapping[str, Path] | None = None) -> None:
        """Copy the table, so later changes to the argument do not reach the locator."""
        self._checkouts = dict(checkouts or {})

    def __call__(self, name: str) -> Path | None:
        """Return the checkout of *name*, or None when the table holds none."""
        return self._checkouts.get(name)
