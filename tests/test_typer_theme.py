# test_typer_theme.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests how a theme colours Typer's help screens."""

import pytest

from sushicore.theme import Theme
from sushicore.typer_theme import apply_typer_theme

pytestmark = pytest.mark.small


def test_apply_points_typer_styles_at_the_theme(monkeypatch):
    rich_utils = pytest.importorskip("typer.rich_utils")
    for name in ("STYLE_OPTION", "STYLE_REQUIRED_LONG", "STYLE_USAGE_COMMAND"):
        monkeypatch.setattr(rich_utils, name, getattr(rich_utils, name, None), raising=False)
    theme = Theme()
    apply_typer_theme(theme)
    assert rich_utils.STYLE_OPTION == theme.cmd
    assert rich_utils.STYLE_USAGE_COMMAND == theme.header
    assert rich_utils.STYLE_REQUIRED_LONG == f"dim {theme.error}"
