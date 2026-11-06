# test_typer_theme.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests how a theme colours Typer's help screens."""

from types import SimpleNamespace

import pytest

from sushicore.theme import Theme
from sushicore.typer_theme import apply_typer_theme

pytestmark = pytest.mark.small


def _themed() -> SimpleNamespace:
    """Return the object a theme was applied to, standing in for Typer's style module."""
    target = SimpleNamespace()
    apply_typer_theme(Theme(), target)
    return target


def test_apply_points_the_option_and_usage_styles_at_the_theme():
    """The option, usage-command and required-long styles follow the theme's tokens."""
    theme = Theme()
    target = _themed()
    assert target.STYLE_OPTION == theme.cmd
    assert target.STYLE_USAGE_COMMAND == theme.header
    assert target.STYLE_REQUIRED_LONG == f"dim {theme.error}"


def test_every_style_the_theme_maps_reaches_typer():
    """All twelve styles are set, not only three."""
    assert sorted(vars(_themed())) == [
        "STYLE_ABORTED", "STYLE_COMMANDS_TABLE_FIRST_COLUMN", "STYLE_DEPRECATED",
        "STYLE_ERRORS_PANEL_BORDER", "STYLE_METAVAR", "STYLE_NEGATIVE_OPTION",
        "STYLE_NEGATIVE_SWITCH", "STYLE_OPTION", "STYLE_REQUIRED_LONG", "STYLE_REQUIRED_SHORT",
        "STYLE_SWITCH", "STYLE_USAGE_COMMAND",
    ]
