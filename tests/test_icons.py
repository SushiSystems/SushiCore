# test_icons.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests the icon sets a console prints before its messages."""

import pytest

import sushicore.icons as icons
from sushicore.errors import ConfigError
from sushicore.icons import IconSet, get_icon_set, known_icon_sets, register_icon_set

pytestmark = pytest.mark.small


def test_merged_takes_known_non_empty_overrides_only():
    merged = IconSet().merged({"info": "i", "warn": "", "unknown": "?"})
    assert merged == IconSet(info="i")


def test_get_icon_set_returns_a_preset():
    assert get_icon_set("minimal").success == "+"


def test_get_icon_set_names_the_known_sets_for_an_unknown_one():
    with pytest.raises(ConfigError, match="Known icon sets: .*minimal"):
        get_icon_set("sparkles")


def test_a_registered_set_is_found_and_listed(monkeypatch):
    monkeypatch.setattr(icons, "_ICON_PRESETS", dict(icons._ICON_PRESETS))
    register_icon_set("arrows", IconSet(info=">"))
    assert get_icon_set("arrows").info == ">"
    assert "arrows" in known_icon_sets()
    assert list(known_icon_sets()) == sorted(known_icon_sets())
