"""sushicore — shared foundation for the Sushi* developer CLIs: sr, se, ss, sa, sb, sd.

Two things live here. A config-driven CLI presentation layer: :func:`build_console`
assembles a :class:`Console` from layered TOML config + environment, using pluggable
:mod:`~sushicore.theme` and :mod:`~sushicore.icons` presets rendered through a pluggable
:mod:`~sushicore.renderer` backend. And the build machinery that decides what reaches a
compiler in five of those repositories: :class:`~sushicore.proc.Runner` (spawning),
:mod:`~sushicore.cmake_cache` (reading CMakeCache.txt), :class:`~sushicore.cmake_driver.CMakeDriver`
(the cmake and ctest invocations) and :mod:`~sushicore.toolchain_args` (compiler and vcpkg
prefix derivation). Each consumer's own ``services/project.py`` keeps its own build policy
and calls into these. Each piece can be registered, overridden, or swapped independently —
see the module docstrings for how.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Sequence

from .config import load_appearance
from .console import Console
from .icons import IconSet, get_icon_set, known_icon_sets, register_icon_set
from .renderer import PlainRenderer, Renderer, RichRenderer
from .theme import Theme, get_theme, known_themes, register_theme
from .typer_theme import apply_typer_theme

__all__ = [
    "Console",
    "Theme",
    "IconSet",
    "Renderer",
    "RichRenderer",
    "PlainRenderer",
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
    if mode == "always":
        return True
    if mode == "never":
        return False
    return sys.stdout.isatty()  # auto


def build_console(config_paths: Sequence[Path] = ()) -> Console:
    """Build a themed :class:`Console` from a repo's own config files.

    ``config_paths`` is the same list of TOML files a repo already resolves
    for its build config (e.g. ``[config.toml, config.local.toml]``, low to
    high precedence) — pass them straight through; only the ``[cli]`` table
    is read here, everything else is ignored.
    """
    spec = load_appearance(list(config_paths))
    theme = get_theme(spec.theme).merged(spec.color_overrides)
    icons = get_icon_set(spec.icons).merged(spec.icon_overrides)
    apply_typer_theme(theme)
    renderer: Renderer = RichRenderer(theme, no_color=not _use_color(spec.color))
    return Console(renderer, theme, icons)
