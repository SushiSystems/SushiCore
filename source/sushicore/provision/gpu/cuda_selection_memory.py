# cuda_selection_memory.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""An architecture probe that answers from a table, with no compiler to run."""

from __future__ import annotations

from typing import Mapping

from .cuda_release import Version


class TableArchitectureProbe:
    """Answers the architectures of a release from the table row of its major version.

    Args:
        architectures: The architectures the compilers of each major version build for.
    """

    def __init__(self, architectures: Mapping[int, frozenset[str]]) -> None:
        """Copy *architectures*, so later changes to the argument do not reach the probe."""
        self._architectures = dict(architectures)

    def __call__(self, version: Version) -> frozenset[str]:
        """Return the architectures of *version*'s major."""
        return self._architectures[version[0]]
