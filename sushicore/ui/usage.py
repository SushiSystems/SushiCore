# usage.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026 Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Draws a command's usage line."""

from __future__ import annotations

from dataclasses import dataclass
from typing import final

from rich.console import RenderableType
from rich.text import Text

from ..theme import Theme


@final
@dataclass(frozen=True, slots=True)
class Usage:
    """Draws ``Usage:`` and the usage string, which is printed literally."""

    usage: str

    def render(self, theme: Theme) -> RenderableType:
        """Return the line with the label muted and the usage in the command style."""
        return Text.assemble(("Usage: ", theme.muted), (self.usage, theme.cmd))
