# typer_theme.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Recolours the help screen Typer renders through Rich to match the theme.

The reasoning is in docs/architecture/OVERVIEW.md, section `typer_theme`.
"""

from __future__ import annotations

from typing import Any

from .theme import Theme


def apply_typer_theme(theme: Theme, target: Any = None) -> None:
    """Point Typer's help-screen colors at ``theme``. No-op if Typer isn't installed.

    Args:
        theme: The theme whose tokens colour the help screen.
        target: The object whose ``STYLE_*`` attributes are set; ``typer.rich_utils`` when None.
    """
    if target is None:
        try:
            import typer.rich_utils as target
        except ImportError:
            return
    rich_utils = target

    rich_utils.STYLE_USAGE_COMMAND = theme.header
    rich_utils.STYLE_OPTION = theme.cmd
    rich_utils.STYLE_SWITCH = theme.success
    rich_utils.STYLE_METAVAR = theme.warn
    rich_utils.STYLE_COMMANDS_TABLE_FIRST_COLUMN = theme.cmd
    rich_utils.STYLE_NEGATIVE_OPTION = theme.error
    rich_utils.STYLE_NEGATIVE_SWITCH = theme.error
    rich_utils.STYLE_REQUIRED_SHORT = theme.error
    rich_utils.STYLE_REQUIRED_LONG = f"dim {theme.error}"
    rich_utils.STYLE_ERRORS_PANEL_BORDER = theme.error
    rich_utils.STYLE_ABORTED = theme.error
    rich_utils.STYLE_DEPRECATED = theme.error
