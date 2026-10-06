# __init__.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Exports the public surface of sushicore and builds a console from layered config.

What the package holds is in docs/architecture/OVERVIEW.md, section `The package`.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Sequence

from .config import load_appearance
from .console import Console
from .icons import IconSet, get_icon_set, known_icon_sets, register_icon_set
from .renderer import JsonRenderer, PlainRenderer, Renderer, RichRenderer
from .terminal_background import is_dark_background
from .theme import Theme, get_theme, known_themes, register_theme
from .typer_theme import apply_typer_theme

__all__ = [
    "Console",
    "Theme",
    "IconSet",
    "Renderer",
    "RichRenderer",
    "PlainRenderer",
    "JsonRenderer",
    "build_console",
    "register_theme",
    "register_icon_set",
    "known_themes",
    "known_icon_sets",
    "get_theme",
    "get_icon_set",
    "apply_typer_theme",
]


def _use_color(mode: str) -> bool:
    """Decide whether colour is on for ``always``, ``never`` or ``auto`` (a TTY stdout)."""
    if mode == "always":
        return True
    if mode == "never":
        return False
    return sys.stdout.isatty()  # auto


def build_console(config_paths: Sequence[Path] = (), *, machine: bool = False) -> Console:
    """Build a themed :class:`Console` from a repo's own config files.

    Args:
        config_paths: The TOML files a repo already resolves for its build config,
            low to high precedence; only the ``[cli]`` table is read.
        machine: When true, render through :class:`JsonRenderer` so stdout carries
            one JSON event per line. Theme and icons are still loaded.
    """
    spec = load_appearance(list(config_paths))
    theme = get_theme(spec.theme).merged(spec.color_overrides)
    icons = get_icon_set(spec.icons).merged(spec.icon_overrides)
    apply_typer_theme(theme)
    renderer: Renderer
    if machine:
        renderer = JsonRenderer()
    else:
        renderer = RichRenderer(theme, no_color=not _use_color(spec.color))
    return Console(renderer, theme, icons, is_dark_background(spec.background, os.environ))
