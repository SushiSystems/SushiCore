# logo.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Draws the Sushi Systems mark, the wordmark beside it and its glow in half-block characters."""

from __future__ import annotations

from dataclasses import dataclass
from typing import final

from rich.style import Style
from rich.text import Text

from ..brand import (
    K_FOREGROUND_KEY,
    K_GLOW_PALETTE,
    K_MARK_PIXELS,
    K_PALETTE,
    K_TRANSPARENT,
    K_WORDMARK_PIXELS,
)
from ..theme import Theme

K_GAP = 2
K_FOREGROUND_COLOUR = "default"

Palette = tuple[tuple[str, str], ...]


def _colours(palette: Palette, glow_palette: Palette, glow: bool) -> dict[str, str]:
    """Return the colour of each pixel key; a key missing from it draws as transparent."""
    colours = dict(palette)
    if glow:
        colours.update(glow_palette)
    colours[K_FOREGROUND_KEY] = K_FOREGROUND_COLOUR
    return colours


def _centred(grid: tuple[str, ...], rows: int) -> list[str]:
    """Return the grid centred in ``rows`` rows, padded with transparent pixels."""
    width = max(len(row) for row in grid)
    above = (rows - len(grid)) // 2
    blank = K_TRANSPARENT * width
    body = [row.ljust(width, K_TRANSPARENT) for row in grid]
    return [blank] * above + body + [blank] * (rows - len(grid) - above)


def _trimmed(grid: tuple[str, ...], colours: dict[str, str]) -> list[str]:
    """Return the grid cut to its coloured pixels, padded at the bottom to an even row count."""
    width = max(len(row) for row in grid)
    rows = [row.ljust(width, K_TRANSPARENT) for row in grid]
    inked_rows = [i for i, row in enumerate(rows) if any(pixel in colours for pixel in row)]
    if not inked_rows:
        return rows
    inked_columns = [c for c in range(width) if any(row[c] in colours for row in rows)]
    first, last = inked_columns[0], inked_columns[-1]
    body = [row[first : last + 1] for row in rows[inked_rows[0] : inked_rows[-1] + 1]]
    if len(body) % 2:
        body.append(K_TRANSPARENT * len(body[0]))
    return body


def _pixels(mark: list[str], wordmark: tuple[str, ...] | None) -> list[str]:
    """Return the grid the logo draws: the mark, the wordmark when given, an even number of rows."""
    height = len(mark)
    if wordmark:
        height = max(height, len(wordmark))
    rows = _centred(tuple(mark), height)
    if wordmark:
        gap = K_TRANSPARENT * K_GAP
        words = _centred(wordmark, height)
        rows = [left + gap + word for left, word in zip(rows, words)]
    if len(rows) % 2:
        rows.append(K_TRANSPARENT * len(rows[0]))
    return rows


def _cell(top: str, bottom: str, colours: dict[str, str]) -> Text:
    """Return the one character that shows a vertical pair of logo pixels."""
    top_colour = colours.get(top)
    bottom_colour = colours.get(bottom)
    if top_colour is None and bottom_colour is None:
        return Text(" ")
    if bottom_colour is None:
        return Text("▀", style=Style(color=top_colour))
    if top_colour is None:
        return Text("▄", style=Style(color=bottom_colour))
    if top_colour == bottom_colour:
        return Text("█", style=Style(color=top_colour))
    return Text("▀", style=Style(color=top_colour, bgcolor=bottom_colour))


@final
@dataclass(frozen=True, slots=True)
class Logo:
    """Draws the brand mark, with the wordmark beside it and a glow behind it when asked.

    The pixel grids and palettes default to the brand's; a caller may pass others, each grid a
    tuple of rows of pixel keys and each palette a tuple of (key, colour) pairs.
    """

    indent: int = 2
    wordmark: bool = True
    glow: bool = False
    mark_pixels: tuple[str, ...] = K_MARK_PIXELS
    wordmark_pixels: tuple[str, ...] = K_WORDMARK_PIXELS
    palette: Palette = tuple(K_PALETTE.items())
    glow_palette: Palette = tuple(K_GLOW_PALETTE.items())

    @property
    def width(self) -> int:
        """Return the columns one row takes, indent included."""
        pixels = self._pixels(self._colours())
        return self.indent + (len(pixels[0]) if pixels else 0)

    def _colours(self) -> dict[str, str]:
        """Return the colour of each pixel key this logo draws."""
        return _colours(self.palette, self.glow_palette, self.glow)

    def _pixels(self, colours: dict[str, str]) -> list[str]:
        """Return the pixel grid this logo draws."""
        return _pixels(_trimmed(self.mark_pixels, colours), self.wordmark_pixels if self.wordmark else None)

    def render(self, theme: Theme) -> Text:
        """Return the logo as styled text, two pixel rows per terminal row."""
        colours = self._colours()
        pixels = self._pixels(colours)
        rows = []
        for top, bottom in zip(pixels[0::2], pixels[1::2]):
            cells = [_cell(upper, lower, colours) for upper, lower in zip(top, bottom)]
            rows.append(Text(" " * self.indent).append_text(Text("").join(cells)))
        return Text("\n").join(rows)
