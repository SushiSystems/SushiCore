"""Draws a bordered body under a title."""

from __future__ import annotations

from dataclasses import dataclass
from typing import final

from rich.console import RenderableType
from rich.panel import Panel as RichPanel
from rich.text import Text

from ..theme import Theme


@final
@dataclass(frozen=True, slots=True)
class Panel:
    """Draws a body inside a border coloured with the theme's panel border."""

    title: str
    body: str

    def render(self, theme: Theme) -> RenderableType:
        """Return the panel; the title and the body keep their Rich markup."""
        return RichPanel(
            self.body,
            title=Text.from_markup(self.title, style=theme.panel_border),
            border_style=theme.panel_border,
        )
