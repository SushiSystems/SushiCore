"""Draws a command's name and its description.

The description is Rich markup in which only a bracket that names a style is a tag, so a
marker such as ``[required]`` stays on the page.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final

from rich.console import Group, RenderableType
from rich.text import Text

from ..markup import escape_unknown_tags
from ..theme import Theme


@final
@dataclass(frozen=True, slots=True)
class Title:
    """Draws a name in the header style with an optional markup description under it."""

    name: str
    description: str = ""

    def render(self, theme: Theme) -> RenderableType:
        """Return the name alone, or the name over its description.

        A bracket in the description that names no style stays as text.
        """
        name = Text(self.name, style=theme.header)
        if not self.description:
            return name
        description = escape_unknown_tags(self.description, theme.as_rich_styles())
        return Group(name, Text.from_markup(description))
