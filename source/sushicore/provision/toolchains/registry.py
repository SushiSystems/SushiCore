# registry.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The ordered set of declared SYCL toolchains and lookups over it."""

from __future__ import annotations

from typing import final

from ...errors import SushiCoreError
from .adaptivecpp import ADAPTIVECPP
from .intel_llvm import INTEL_LLVM
from .oneapi import ONEAPI
from .toolchain import Toolchain


class DuplicateToolchainError(SushiCoreError, ValueError):
    """Reports two toolchains that share a key or a selection field."""


@final
class ToolchainRegistry:
    """An ordered, duplicate-free set of :class:`Toolchain`.

    Args:
        toolchains: The toolchains to register, in install order.

    Raises:
        DuplicateToolchainError: When two toolchains share a key or a selection field.
    """

    def __init__(self, toolchains: tuple[Toolchain, ...]) -> None:
        """Validate and store *toolchains*, indexing them by key."""
        by_key: dict[str, Toolchain] = {}
        fields: set[str] = set()
        for toolchain in toolchains:
            if toolchain.key in by_key:
                raise DuplicateToolchainError(f"Duplicate toolchain key: '{toolchain.key}'")
            if toolchain.selection_field in fields:
                raise DuplicateToolchainError(f"Duplicate toolchain selection field: '{toolchain.selection_field}'")
            by_key[toolchain.key] = toolchain
            fields.add(toolchain.selection_field)
        self._toolchains = tuple(toolchains)
        self._by_key = by_key

    def all(self) -> tuple[Toolchain, ...]:
        """Return every registered toolchain, in install order."""
        return self._toolchains

    def for_key(self, key: str) -> Toolchain | None:
        """Return the toolchain named *key*, or None."""
        return self._by_key.get(key)


TOOLCHAINS: tuple[Toolchain, ...] = (INTEL_LLVM, ADAPTIVECPP, ONEAPI)

DEFAULT_REGISTRY = ToolchainRegistry(TOOLCHAINS)
