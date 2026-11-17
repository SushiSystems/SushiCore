# __init__.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Exports the public surface of sushicore.

What the package holds is in docs/architecture/OVERVIEW.md, section `The package`.
"""

from __future__ import annotations

from .console import Console
from .console_builder import build_console
from .icons import IconSet, get_icon_set, known_icon_sets, register_icon_set
from .renderer import JsonRenderer, PlainRenderer, Renderer, RichRenderer
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
