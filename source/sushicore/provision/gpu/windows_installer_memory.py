# windows_installer_memory.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""A machine environment held in a dictionary, in place of the registry."""

from __future__ import annotations

from typing import Mapping


class InMemoryMachineEnvironment:
    """Serves machine environment variables from the values it was given.

    Args:
        variables: The machine value of each variable that is set.
    """

    def __init__(self, variables: Mapping[str, str] | None = None) -> None:
        """Copy *variables*, so later changes to the argument do not reach it."""
        self._variables = dict(variables or {})

    def read(self, name: str) -> str | None:
        """Return the machine value of *name*, or None when it is unset or empty."""
        return self._variables.get(name) or None
