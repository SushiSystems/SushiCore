# cmake_tool_config.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The configuration fields the cmake driver reads."""

from __future__ import annotations

from typing import Protocol


class CMakeToolConfig(Protocol):
    """The tool paths and the path expansion a CMake driver reads from a CLI's config."""

    @property
    def cmake_exe(self) -> str:
        """The configured cmake executable; empty when the PATH one is meant."""
        ...

    @property
    def ctest_exe(self) -> str:
        """The configured ctest executable; empty when the PATH one is meant."""
        ...

    @property
    def doxygen_exe(self) -> str:
        """The configured doxygen executable; empty when the PATH one is meant."""
        ...

    def expand(self, value: str) -> str:
        """Expand ``~`` and environment variables in a path value."""
        ...
