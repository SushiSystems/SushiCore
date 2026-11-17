# test_console_builder.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""A console built from config files takes its background and theme from them."""

from __future__ import annotations

import pytest

from sushicore.console_builder import build_console
from sushicore.environment_memory import MemoryEnvironment
from sushicore.files_memory import MemoryFiles
from sushicore.theme import get_theme

pytestmark = pytest.mark.medium


@pytest.fixture(autouse=True)
def _no_appearance_environment(monkeypatch):
    """Remove every variable the appearance reads so each test states the environment it needs."""
    for name in ("COLORFGBG", "SUSHI_CLI_BACKGROUND", "SUSHI_CLI_THEME", "SUSHI_CLI_ICONS",
                 "SUSHI_CLI_COLOR", "NO_COLOR"):
        monkeypatch.delenv(name, raising=False)


def _config(tmp_path, body: str):
    """Write *body* as a config file and return its path."""
    path = tmp_path / "config.toml"
    path.write_text(body, encoding="utf-8")
    return path


def test_build_console_takes_the_background_from_the_config(tmp_path):
    path = _config(tmp_path, '[cli]\nbackground = "dark"\n')
    assert build_console([path]).dark_background


def test_build_console_falls_back_to_colorfgbg(monkeypatch):
    monkeypatch.setenv("COLORFGBG", "15;0")
    assert build_console([]).dark_background


def test_build_console_without_a_setting_or_colorfgbg_is_not_dark():
    assert not build_console([]).dark_background


def test_a_console_built_from_a_bad_theme_says_so(tmp_path, capsys):
    build_console([_config(tmp_path, '[cli]\ntheme = "neon"\n')], machine=True)
    out = capsys.readouterr().out
    assert '"level":"warn"' in out
    assert "Unknown CLI theme 'neon'" in out


def test_a_console_built_from_a_bad_theme_takes_the_default_theme(tmp_path):
    console = build_console([_config(tmp_path, '[cli]\ntheme = "neon"\n')], machine=True)
    assert console.theme == get_theme("default")


def test_build_console_reads_the_background_from_the_environment_given():
    console = build_console([], environment=MemoryEnvironment({"SUSHI_CLI_BACKGROUND": "dark"}),
                            files=MemoryFiles())
    assert console.dark_background is True
