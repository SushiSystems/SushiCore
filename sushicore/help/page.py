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


@final
@dataclass(frozen=True, slots=True)
class HelpPage:
    """Draws one help screen as a stack of blocks."""

    model: HelpModel
    logo: Component | None = None

    def render(self, theme: Theme) -> RenderableType:
        """Return the blocks in order, one blank line between neighbours."""
        parts: list[RenderableType] = []
        for block in self._blocks():
            if parts:
                parts.append(Text(""))
            parts.append(block.render(theme))
        return Group(*parts)

    def _blocks(self) -> list[Component]:
        """Return the components to draw: logo, title, usage, then each non-empty list."""
        model = self.model
        blocks: list[Component] = []
        if self.logo is not None and model.is_root:
            blocks.append(self.logo)
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
