# test_read_toml.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests how the workspace reads a TOML file."""

from datetime import date

import pytest

from sushicore.errors import ConfigError

from sushicore.workspace import read_toml



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
