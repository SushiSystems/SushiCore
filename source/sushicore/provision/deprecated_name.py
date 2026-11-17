# deprecated_name.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Warns that a name restored for one release is deprecated, pointing at its caller."""

from __future__ import annotations

import warnings


def warn_deprecated(name: str, replacement: str, *, depth: int = 1) -> None:
    """Warn that *name* is deprecated in favour of *replacement*.

    Args:
        name: The old name, as its caller wrote it.
        replacement: What to use instead.
        depth: How many frames sit between the code that calls this and the code the warning
            should point at; 1 points at the caller of the function that called this.
    """
    warnings.warn(f"{name} is deprecated; use {replacement}", DeprecationWarning,
                  stacklevel=depth + 2)
