# test_icon_registry.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests the registry of named icon sets."""

from __future__ import annotations

import pytest

from sushicore.errors import ConfigError
from sushicore.icon_registry import IconRegistry
from sushicore.icons import IconSet

pytestmark = pytest.mark.small


def test_a_registered_set_is_found_by_name():
    registry = IconRegistry()
    registry.register("arrows", IconSet(info=">"))
    assert registry.get("arrows").info == ">"


def test_an_unknown_name_raises_a_config_error_naming_the_known_sets():
    with pytest.raises(ConfigError, match="Known icon sets: arrows"):
        IconRegistry({"arrows": IconSet()}).get("sparkles")


def test_known_lists_the_names_sorted():
    assert IconRegistry({"zebra": IconSet(), "arrows": IconSet()}).known() == ("arrows", "zebra")


def test_a_registry_copies_the_presets_it_starts_from():
    presets = {"a": IconSet()}
    registry = IconRegistry(presets)
    registry.register("b", IconSet())
    assert tuple(presets) == ("a",)
