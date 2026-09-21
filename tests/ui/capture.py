"""Renders a component to the text a terminal would show, with or without colour."""

from __future__ import annotations

import io

from rich.console import Console

from sushicore.theme import Theme
from sushicore.ui.component import Component


def capture_raw(component: Component, width: int = 60, theme: Theme | None = None) -> str:
    """Return the component's plain text at ``width`` columns, trailing spaces kept."""
    stream = io.StringIO()
    console = Console(
        file=stream,
        width=width,
        color_system=None,
        force_terminal=False,
        legacy_windows=False,
        no_color=False,
    )
    console.print(component.render(theme or Theme()))
    return stream.getvalue()


def capture(component: Component, width: int = 60, theme: Theme | None = None) -> str:
    """Return the component's plain text at ``width`` columns, trailing spaces stripped."""
    raw = capture_raw(component, width, theme)
    return "\n".join(line.rstrip() for line in raw.split("\n"))


def capture_ansi(
    component: Component,
    width: int = 60,
    theme: Theme | None = None,
    color_system: str = "truecolor",
) -> str:
    """Return the component's output as a terminal of ``color_system`` would receive it."""
    stream = io.StringIO()
    console = Console(
        file=stream,
        width=width,
        color_system=color_system,
        force_terminal=True,
        legacy_windows=False,
        no_color=False,
    )
    console.print(component.render(theme or Theme()))
    return stream.getvalue()
