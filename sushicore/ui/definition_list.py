"""Draws a heading over a two-column list of terms and their text.

A term is literal. An entry's text is Rich markup in which only a bracket that names a
style is a tag, so a marker such as ``[required]`` stays on the page.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final

from rich.console import Group, RenderableType
from rich.padding import Padding
from rich.table import Table as RichTable
from rich.text import Text

from ..markup import escape_unknown_tags
from ..theme import Theme

K_INDENT = 2
K_COLUMN_GAP = 2


@final
@dataclass(frozen=True, slots=True)
class DefinitionList:
    """Draws commands, arguments, options or examples: a term, then what it means."""

    heading: str
    entries: tuple[tuple[str, str], ...]

    def render(self, theme: Theme) -> RenderableType:
        """Return the heading and the indented grid; terms are literal, text is markup.

        A term takes the theme's command style with bold switched off, so the heading is the
        heavier of the two. A bracket in the text that names no style stays as text.
        """
        term_style = f"{theme.cmd} not bold"
        styles = theme.as_rich_styles()
        grid = RichTable.grid(padding=(0, K_COLUMN_GAP))
        grid.add_column(no_wrap=True)
        grid.add_column()
        for term, text in self.entries:
            markup = Text.from_markup(escape_unknown_tags(text, styles))
            grid.add_row(Text(term, style=term_style), markup)
        return Group(
            Text(self.heading, style=theme.header),
            Padding(grid, (0, 0, 0, K_INDENT), expand=False),
        )
