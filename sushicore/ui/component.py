# component.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""The one shape every terminal component has."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from rich.console import RenderableType

from ..theme import Theme


@runtime_checkable
class Component(Protocol):
    """Describes a piece of terminal output that draws itself from a theme."""

    def render(self, theme: Theme) -> RenderableType:
        """Return the Rich renderable this component draws in ``theme``."""
        ...
