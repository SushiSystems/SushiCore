# test_config_in_memory.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Appearance loads from an in-memory environment and files, with no disk."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore import build_console
from sushicore.config import load_appearance
from sushicore.environment_memory import MemoryEnvironment
from sushicore.errors import ConfigError
from sushicore.files_memory import MemoryFiles

pytestmark = pytest.mark.small

K_CONFIG = Path("mem") / "module" / "cli" / "config.toml"


def test_the_appearance_comes_from_the_files_and_the_environment_given():
    files = MemoryFiles({K_CONFIG: '[cli]\ntheme = "muted"\nicons = "minimal"\n'})
    spec = load_appearance([K_CONFIG], environment=MemoryEnvironment({"SUSHI_CLI_ICONS": "text"}),
                           files=files)
    assert (spec.theme, spec.icons) == ("muted", "text")


def test_no_color_in_the_environment_given_turns_colour_off():
    spec = load_appearance([], environment=MemoryEnvironment({"NO_COLOR": ""}), files=MemoryFiles())
    assert spec.color == "never"


def test_a_malformed_config_in_memory_raises_a_config_error_naming_the_file():
    files = MemoryFiles({K_CONFIG: "[cli\ntheme = "})
    with pytest.raises(ConfigError, match="config.toml"):
        load_appearance([K_CONFIG], environment=MemoryEnvironment(), files=files)


def test_an_unknown_theme_in_memory_warns_and_falls_back():
    spec = load_appearance([], environment=MemoryEnvironment({"SUSHI_CLI_THEME": "nope"}),
                           files=MemoryFiles())
    assert spec.theme == "default" and "Unknown CLI theme 'nope'" in spec.warnings[0]


def test_build_console_reads_the_background_from_the_environment_given():
    console = build_console([], environment=MemoryEnvironment({"SUSHI_CLI_BACKGROUND": "dark"}),
                            files=MemoryFiles())
    assert console.dark_background is True
