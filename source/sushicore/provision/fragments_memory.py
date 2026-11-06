# fragments_memory.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""A dependency source that serves a list given in memory and reads no fragment file."""

from __future__ import annotations

from typing import Iterable, Mapping

from .fragments import Dependency, IDependencySource


class InMemoryDependencySource(IDependencySource):
    """Serves the dependencies and the module-to-modules map it was given.

    Args:
        dependencies: Every declared dependency, regardless of platform.
        depends_on: The owners each owner directly builds on.
    """

    def __init__(self, dependencies: Iterable[Dependency],
                 depends_on: Mapping[str, Iterable[str]] | None = None) -> None:
        """Copy the dependencies and the map, so later changes to the arguments do not reach it."""
        self._dependencies = list(dependencies)
        self._depends_on = {owner: list(owners) for owner, owners in (depends_on or {}).items()}

    def all(self) -> list[Dependency]:
        """Return every dependency, in the order given."""
        return list(self._dependencies)

    def depends_on(self, owner: str) -> list[str]:
        """Return the owners *owner* directly builds on; empty for an unknown owner."""
        return list(self._depends_on.get(owner, []))
