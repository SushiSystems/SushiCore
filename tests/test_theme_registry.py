# test_theme_registry.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests the registry of named themes."""

from __future__ import annotations

import pytest

from sushicore.errors import ConfigError
from sushicore import theme as theme_module
from sushicore.theme import Theme, register_theme
from sushicore.theme_registry import ThemeRegistry

pytestmark = pytest.mark.small


def test_a_registered_theme_is_found_by_name():
    registry = ThemeRegistry()
    theme = Theme(info="red")
    registry.register("red", theme)
    assert registry.get("red") is theme


def test_an_unknown_name_raises_a_config_error_naming_the_known_themes():
    with pytest.raises(ConfigError, match="Known themes: mine"):
        ThemeRegistry({"mine": Theme()}).get("other")


def test_known_lists_the_names_sorted():
    assert ThemeRegistry({"zebra": Theme(), "arrows": Theme()}).known() == ("arrows", "zebra")


def test_register_theme_warns_and_adds_to_the_default_registry(monkeypatch):
    default = ThemeRegistry()
    monkeypatch.setattr(theme_module, "DEFAULT_THEME_REGISTRY", default)
    with pytest.warns(DeprecationWarning, match="register_theme"):
        register_theme("shim-test", Theme(info="green"))
    assert default.get("shim-test").info == "green"
