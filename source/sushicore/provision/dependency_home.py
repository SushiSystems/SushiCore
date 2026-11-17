# dependency_home.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Holds the provider a caller binds as the dependency root, in place of a module-level binding."""

from __future__ import annotations

import typing
from collections.abc import Callable
from pathlib import Path


@typing.final
class DependencyHome:
    """Holds the provider of the dependency root; ``None`` means the env var, then the default."""

    def __init__(self, provider: Callable[[], Path] | None = None) -> None:
        """Hold *provider*, or none when omitted."""
        self._provider = provider

    @property
    def provider(self) -> Callable[[], Path] | None:
        """Return the bound provider, or ``None`` when nothing is bound."""
        return self._provider

    def bind(self, provider: Callable[[], Path] | None) -> None:
        """Make *provider* the source of the root; ``None`` unbinds."""
        self._provider = provider


DEFAULT_HOME = DependencyHome()
"""The home every root lookup reads when its caller passes none; set by the deprecated ``bind_root``."""
