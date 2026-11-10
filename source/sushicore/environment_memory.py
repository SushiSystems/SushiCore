# environment_memory.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Environment variables held in a dictionary, keeping the promise of the `Environment` port."""

from __future__ import annotations

from typing import Mapping


class MemoryEnvironment:
    """Variables held by name; nothing is read from the process."""

    def __init__(self, variables: Mapping[str, str] | None = None) -> None:
        """Keeps the variables given, by name."""
        self.variables: dict[str, str] = dict(variables or {})

    def get(self, name: str, default: str | None = None) -> str | None:
        """Returns a variable's value, or the default when it is not set."""
        return self.variables.get(name, default)

    def has(self, name: str) -> bool:
        """Returns whether a variable is set, an empty value included."""
        return name in self.variables
