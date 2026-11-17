# test_layered_toml.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests how a TOML file is read, merged by platform and found by walking up to a marker."""

from datetime import date

import pytest

from sushicore.errors import ConfigError

from sushicore.layered_toml import (
    has_marker,
    load_layered,
    merge_platform_table,
    read_toml,
    walk_up,
)
from sushicore.environment_memory import MemoryEnvironment



pytestmark = pytest.mark.medium



K_REMOVED = date(2027, 3, 25)



def test_read_toml_reports_a_malformed_file_as_a_config_error(tmp_path):
    """A file that is not TOML raises a ConfigError that names the file."""
    path = tmp_path / "config.toml"
    path.write_text("[cli\ncolor = ", encoding="utf-8")
    with pytest.raises(ConfigError) as caught:
        read_toml(path)
    assert str(path) in str(caught.value)
    assert isinstance(caught.value, ValueError)


def test_the_platform_table_wins_over_the_common_one_and_nested_tables_are_dropped():
    """Check that a repeated key takes the platform value and other tables are dropped."""
    doc = {"tool": {"cmake": "a", "generator": "Ninja", "other": {"x": 1},
                    "linux": {"cmake": "b", "extra": {"y": 2}}}}
    assert merge_platform_table(doc, "linux") == {"cmake": "b", "generator": "Ninja"}


def test_a_later_file_and_then_an_environment_variable_override_an_earlier_value(tmp_path):
    """Check the layer order: low file, high file, environment, then bool coercion."""
    low = tmp_path / "low.toml"
    high = tmp_path / "high.toml"
    low.write_text('[tool]\ncmake = "low"\nninja = "low"\nverbose = "yes"\n', encoding="utf-8")
    high.write_text('[tool]\ncmake = "high"\n', encoding="utf-8")
    values = load_layered([low, high], "linux", {"ninja": "SUSHI_NINJA"}, bool_keys=["verbose"],
                          environment=MemoryEnvironment({"SUSHI_NINJA": "env"}))
    assert values == {"cmake": "high", "ninja": "env", "verbose": True}


def test_walk_up_returns_the_nearest_ancestor_holding_the_marker(tmp_path):
    """Check that the walk starts at the given folder and stops at the nearest marker."""
    (tmp_path / ".marker").mkdir()
    deep = tmp_path / "a" / "b"
    deep.mkdir(parents=True)
    assert walk_up(deep, has_marker(".marker")) == tmp_path.resolve()


def test_walk_up_is_none_when_no_ancestor_holds_the_marker(tmp_path):
    """Check that a marker nobody holds gives None."""
    assert walk_up(tmp_path, has_marker(".no-such-marker-xyz")) is None
