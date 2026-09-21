"""Draws a heading over a two-column list of terms and their text."""

from __future__ import annotations

from dataclasses import dataclass
from typing import final

from rich.console import Group, RenderableType
from rich.padding import Padding
from rich.table import Table as RichTable
from rich.text import Text

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
        """Return the heading and the indented grid; terms are literal, text is markup."""
        grid = RichTable.grid(padding=(0, K_COLUMN_GAP))
        grid.add_column(no_wrap=True)
        grid.add_column()
        for term, text in self.entries:
            grid.add_row(Text(term, style=theme.cmd), Text.from_markup(text))
        return Group(
            Text(self.heading, style=theme.header),
            Padding(grid, (0, 0, 0, K_INDENT), expand=False),
        )
