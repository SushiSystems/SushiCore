# user_environment_memory.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""A registry key that holds the user's variables in memory and touches no registry."""

from __future__ import annotations


class InMemoryEnvironmentKey:
    """Holds values in a dict and logs when it is closed, as an opened registry key would.

    Args:
        values: The variables the key holds; shared with the caller, so it can be read after a write.
        log: The list the key appends ``close`` to; shared with the caller.
    """

    def __init__(self, values: dict[str, str], log: list[str]) -> None:
        """Share *values* and *log* with the caller."""
        self._values = values
        self._log = log

    def query(self, name: str) -> str | None:
        """Return the value stored under *name*, or None when there is none."""
        return self._values.get(name)

    def set(self, name: str, value: str) -> None:
        """Store *value* under *name*."""
        self._values[name] = value

    def delete(self, name: str) -> None:
        """Delete *name*; a name that is absent is not an error."""
        self._values.pop(name, None)

    def close(self) -> None:
        """Record that the key was released."""
        self._log.append("close")
