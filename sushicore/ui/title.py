"""Draws a command's name and its description."""

from __future__ import annotations

from dataclasses import dataclass
from typing import final

from rich.console import Group, RenderableType
from rich.text import Text

from ..theme import Theme


@final
@dataclass(frozen=True, slots=True)
class Title:
    """Draws a name in the header style with an optional markup description under it."""

    name: str
    description: str = ""

    def render(self, theme: Theme) -> RenderableType:
        """Return the name alone, or the name over its description."""
        name = Text(self.name, style=theme.header)
        if not self.description:
            return name
        return Group(name, Text.from_markup(self.description))
