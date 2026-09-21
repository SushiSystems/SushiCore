"""Lays a HelpModel out as components, in the order a help screen shows them."""

from __future__ import annotations

from dataclasses import dataclass
from typing import final

from rich.console import Group, RenderableType
from rich.text import Text

from ..theme import Theme
from ..ui.component import Component
from ..ui.definition_list import DefinitionList
from ..ui.title import Title
from ..ui.usage import Usage
from .model import HelpModel

K_ARGUMENTS = "Arguments"
K_OPTIONS = "Options"
K_EXAMPLES = "Examples"
K_LOGO_MARGIN = 1


def _blank_lines(count: int) -> list[RenderableType]:
    """Return ``count`` empty lines."""
    return [Text("") for _ in range(count)]


@final
@dataclass(frozen=True, slots=True)
class HelpPage:
    """Draws one help screen as a stack of blocks."""

    model: HelpModel
    logo: Component | None = None

    def render(self, theme: Theme) -> RenderableType:
        """Return the blocks in order, one blank line between neighbours, air around a logo."""
        has_logo = self._root_logo() is not None
        parts: list[RenderableType] = _blank_lines(K_LOGO_MARGIN if has_logo else 0)
        for index, block in enumerate(self._blocks()):
            if index:
                extra = K_LOGO_MARGIN if has_logo and index == 1 else 0
                parts += _blank_lines(1 + extra)
            parts.append(block.render(theme))
        return Group(*parts)

    def _root_logo(self) -> Component | None:
        """Return the logo when this page is the root page, else nothing."""
        return self.logo if self.model.is_root else None

    def _blocks(self) -> list[Component]:
        """Return the components to draw: logo, title, usage, then each non-empty list."""
        model = self.model
        blocks: list[Component] = []
        logo = self._root_logo()
        if logo is not None:
            blocks.append(logo)
        blocks.append(Title(model.name, model.description))
        blocks.append(Usage(model.usage))
        blocks += [DefinitionList(s.heading, s.entries) for s in model.commands]
        for heading, entries in (
            (K_ARGUMENTS, model.arguments),
            (K_OPTIONS, model.options),
            (K_EXAMPLES, model.examples),
        ):
            if entries:
                blocks.append(DefinitionList(heading, entries))
        return blocks
