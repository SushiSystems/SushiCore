"""Draws rows under one header rule, with no frame around them."""

from __future__ import annotations

from dataclasses import dataclass
from typing import final

from rich import box
from rich.console import RenderableType
from rich.table import Table as RichTable

from ..theme import Theme


@final
@dataclass(frozen=True, slots=True)
class Table:
    """Draws a titled table of string cells."""

    columns: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]
    title: str = ""

    def render(self, theme: Theme) -> RenderableType:
        """Return the table: header row, a rule in the muted style, then the rows."""
        table = RichTable(
            title=self.title or None,
            title_justify="left",
            title_style=theme.info,
            box=box.SIMPLE_HEAD,
            show_edge=False,
            pad_edge=False,
            header_style=theme.header,
            border_style=theme.muted,
        )
        for column in self.columns:
            table.add_column(column)
        for row in self.rows:
            table.add_row(*row)
        return table
