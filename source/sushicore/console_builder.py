# console_builder.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Builds a themed console from a repository's own config files."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Sequence

from .config import load_appearance
from .console import Console
from .environment import Environment, ProcessEnvironment
from .files import Files
from .icon_registry import IconRegistry
from .icons import DEFAULT_ICON_REGISTRY
from .renderer import JsonRenderer, Renderer, RichRenderer
from .terminal_background import is_dark_background
from .theme import DEFAULT_THEME_REGISTRY
from .theme_registry import ThemeRegistry
from .typer_theme import apply_typer_theme


def _use_color(mode: str) -> bool:
    """Decide whether colour is on for ``always``, ``never`` or ``auto`` (a TTY stdout)."""
    if mode == "always":
        return True
    if mode == "never":
        return False
    return sys.stdout.isatty()  # auto


def build_console(config_paths: Sequence[Path] = (), *, machine: bool = False,
                  environment: Environment | None = None, files: Files | None = None,
                  theme_registry: ThemeRegistry | None = None,
                  icon_registry: IconRegistry | None = None) -> Console:
    """Build a themed :class:`Console` from a repo's own config files.

    Args:
        config_paths: The TOML files of the build config, low to high precedence.
        machine: When true, render through :class:`JsonRenderer`, one JSON event per line.
        environment: The variables the appearance is read from; the process's when None.
        files: The file system the config files are read through; the disk when None.
        theme_registry: The themes a config may name; the default registry when None.
    """
    environment = ProcessEnvironment() if environment is None else environment
    themes = theme_registry or DEFAULT_THEME_REGISTRY
    icon_sets = icon_registry or DEFAULT_ICON_REGISTRY
    spec = load_appearance(list(config_paths), environment=environment, files=files,
                           theme_registry=themes, icon_registry=icon_sets)
    theme = themes.get(spec.theme).merged(spec.color_overrides)
    icons = icon_sets.get(spec.icons).merged(spec.icon_overrides)
    apply_typer_theme(theme)
    renderer: Renderer
    if machine:
        renderer = JsonRenderer()
    else:
        renderer = RichRenderer(theme, no_color=not _use_color(spec.color))
    console = Console(renderer, theme, icons, is_dark_background(spec.background, environment))
    for warning in spec.warnings:
        console.warn(warning)
    return console
