# header.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Draws a blank line and a titled rule."""

from __future__ import annotations

from dataclasses import dataclass
from typing import final

from rich.console import Group, RenderableType
from rich.rule import Rule
from rich.text import Text

from ..theme import Theme


@final
@dataclass(frozen=True, slots=True)
class Header:
    """Draws a section header: a blank line, then a rule holding the title."""

    title: str

    def render(self, theme: Theme) -> RenderableType:
        """Return the header; the title keeps its Rich markup."""
        return Group(
            Text(""),
            Rule(Text.from_markup(self.title, style=theme.header), style=theme.rule_line),
        )
