"""Draws rows under one header rule, flat or grouped, with no frame around them.

A cell whose whole text is a status word is coloured from the theme; the map
from word to theme field is ``K_STATUS_STYLES``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final

from rich import box
from rich.cells import cell_len
from rich.console import Group, RenderableType
from rich.padding import Padding
from rich.rule import Rule
from rich.table import Table as RichTable
from rich.text import Text

from ..theme import Theme

K_INDENT = 2
K_COLUMN_GAP = 2
K_EMPTY_GROUP = "-"

K_STATUS_STYLES: dict[str, str] = {
    "OK": "success",
    "MISSING": "error",
    "FAIL": "error",
    "FAILED": "error",
    "ERROR": "error",
    "WARN": "warn",
    "WARNING": "warn",
    "NOT NEEDED": "muted",
    "SKIPPED": "muted",
    "N/A": "muted",
}


def _cell(text: str, theme: Theme) -> Text:
    """Return the cell as text: a status word in its theme style, anything else as markup."""
    field = K_STATUS_STYLES.get(text.upper())
    if field is None:
        return Text.from_markup(text)
    return Text(text, style=getattr(theme, field))


def _grouped_rows(
    rows: tuple[tuple[str, ...], ...], index: int
) -> dict[str, list[tuple[str, ...]]]:
    """Return the rows without column ``index``, bucketed by its value in order of appearance."""
    groups: dict[str, list[tuple[str, ...]]] = {}
    for row in rows:
        value = row[index] if index < len(row) and row[index] else K_EMPTY_GROUP
        groups.setdefault(value, []).append(row[:index] + row[index + 1 :])
    return groups


def _fixed_widths(cell_rows: list[list[Text]]) -> list[int]:
    """Return the width of every column but the last, as wide as its widest cell."""
    if not cell_rows:
        return []
    columns = max(len(row) for row in cell_rows)
    return [
        max((cell_len(row[column].plain) for row in cell_rows if column < len(row)), default=0)
        for column in range(columns - 1)
    ]


def _grid(cell_rows: list[list[Text]], widths: list[int]) -> RichTable:
    """Return a borderless grid whose leading columns hold ``widths`` and whose last one wraps."""
    grid = RichTable.grid(padding=(0, K_COLUMN_GAP))
    for width in widths:
        grid.add_column(width=width, no_wrap=True)
    grid.add_column(overflow="fold")
    for row in cell_rows:
        grid.add_row(*row)
    return grid


@final
@dataclass(frozen=True, slots=True)
class Table:
    """Draws a titled table of string cells, optionally grouped under one column's values."""

    columns: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]
    title: str = ""
    group_by: str | None = None

    def __post_init__(self) -> None:
        """Reject a grouping column that is not one of the table's own columns.

        Raises:
            ValueError: When ``group_by`` names no column.
        """
        if self.group_by is not None and self.group_by not in self.columns:
            names = ", ".join(self.columns)
            raise ValueError(f"group_by '{self.group_by}' names no column; the columns are {names}")

    def render(self, theme: Theme) -> RenderableType:
        """Return the flat table, or the grouped one when ``group_by`` names a column."""
        if self.group_by is None:
            return self._flat(theme)
        return self._grouped(theme)

    def _flat(self, theme: Theme) -> RenderableType:
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
            table.add_row(*(_cell(text, theme) for text in row))
        return table

    def _grouped(self, theme: Theme) -> RenderableType:
        """Return a heading per group over rows that share one set of column widths."""
        index = self.columns.index(self.group_by)
        headers = [
            Text(name, style=theme.header)
            for position, name in enumerate(self.columns)
            if position != index
        ]
        groups = {
            value: [[_cell(text, theme) for text in row] for row in rows]
            for value, rows in _grouped_rows(self.rows, index).items()
        }
        widths = _fixed_widths([headers, *(row for rows in groups.values() for row in rows)])
        parts: list[RenderableType] = []
        if self.title:
            parts += [Text(self.title, style=theme.info), Text("")]
        parts += [self._indented(_grid([headers], widths)), Rule(style=theme.muted)]
        for position, (value, rows) in enumerate(groups.items()):
            if position:
                parts.append(Text(""))
            parts += [Text(value, style=theme.header), self._indented(_grid(rows, widths))]
        return Group(*parts)

    @staticmethod
    def _indented(grid: RichTable) -> RenderableType:
        """Return the grid pushed right by the group indent."""
        return Padding(grid, (0, 0, 0, K_INDENT))
