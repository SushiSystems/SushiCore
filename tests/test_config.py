# test_config.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""The background setting travels from a TOML file and the environment to the console."""

import io

import pytest

from sushicore import build_console
from sushicore.config import load_appearance
from sushicore.console import Console
from sushicore.icons import IconSet
from sushicore.renderer import PlainRenderer
from sushicore.theme import Theme


pytestmark = pytest.mark.medium


@pytest.fixture(autouse=True)
def _no_background_environment(monkeypatch):
    """Remove both background variables so each test states the environment it needs."""
    monkeypatch.delenv("COLORFGBG", raising=False)
    monkeypatch.delenv("SUSHI_CLI_BACKGROUND", raising=False)


def _config(tmp_path, body: str):
    path = tmp_path / "config.toml"
    path.write_text(body, encoding="utf-8")
    return path


def test_background_defaults_to_auto():
    assert load_appearance([]).background == "auto"


def test_the_cli_table_sets_the_background(tmp_path):
    path = _config(tmp_path, '[cli]\nbackground = "dark"\n')
    assert load_appearance([path]).background == "dark"


def test_the_platform_table_overrides_the_common_one(tmp_path, monkeypatch):
    monkeypatch.setattr("platform.system", lambda: "Windows")
    path = _config(tmp_path, '[cli]\nbackground = "light"\n\n[cli.windows]\nbackground = "dark"\n')
    assert load_appearance([path]).background == "dark"


def test_the_environment_overrides_the_file(tmp_path, monkeypatch):
    monkeypatch.setenv("SUSHI_CLI_BACKGROUND", "light")
    path = _config(tmp_path, '[cli]\nbackground = "dark"\n')
    assert load_appearance([path]).background == "light"


def test_an_unknown_background_falls_back_to_auto(tmp_path):
    path = _config(tmp_path, '[cli]\nbackground = "sepia"\n')
    assert load_appearance([path]).background == "auto"


def test_a_console_reports_the_background_it_was_built_with():
    console = Console(PlainRenderer(stream=io.StringIO()), Theme(), IconSet(), dark_background=True)
    assert console.dark_background


def test_a_console_assumes_a_light_background_by_default():
    assert not Console(PlainRenderer(stream=io.StringIO()), Theme(), IconSet()).dark_background


def test_build_console_takes_the_background_from_the_config(tmp_path):
    path = _config(tmp_path, '[cli]\nbackground = "dark"\n')
    assert build_console([path]).dark_background


def test_build_console_falls_back_to_colorfgbg(monkeypatch):
    monkeypatch.setenv("COLORFGBG", "15;0")
    assert build_console([]).dark_background


def test_build_console_without_a_setting_or_colorfgbg_is_not_dark():
    assert not build_console([]).dark_background


@pytest.fixture
def _clean_appearance_environment(monkeypatch):
    for name in ("SUSHI_CLI_THEME", "SUSHI_CLI_ICONS", "SUSHI_CLI_COLOR", "NO_COLOR"):
        monkeypatch.delenv(name, raising=False)


@pytest.mark.parametrize("key, bad, fallback", [
    ("theme", "neon", "default"),
    ("icons", "sparkly", "text"),
    ("color", "rainbow", "auto"),
    ("background", "sepia", "auto"),
])
def test_every_unknown_appearance_value_falls_back_and_warns_once(
        tmp_path, _clean_appearance_environment, key, bad, fallback):
    spec = load_appearance([_config(tmp_path, f'[cli]\n{key} = "{bad}"\n')])
    assert getattr(spec, key) == fallback
    assert len(spec.warnings) == 1
    assert f"Unknown CLI {key} '{bad}'" in spec.warnings[0]
    assert f"using '{fallback}'" in spec.warnings[0]


def test_known_values_raise_no_warning(tmp_path, _clean_appearance_environment):
    spec = load_appearance([_config(tmp_path, '[cli]\ntheme = "muted"\nicons = "minimal"\ncolor = "never"\n')])
    assert (spec.theme, spec.icons, spec.color, spec.warnings) == ("muted", "minimal", "never", [])


def test_a_bad_value_from_the_environment_is_handled_the_same_way(monkeypatch, _clean_appearance_environment):
    monkeypatch.setenv("SUSHI_CLI_THEME", "neon")
    spec = load_appearance([])
    assert spec.theme == "default"
    assert "Unknown CLI theme 'neon'" in spec.warnings[0]


def test_a_console_built_from_a_bad_theme_works_and_says_so(tmp_path, _clean_appearance_environment, capsys):
    console = build_console([_config(tmp_path, '[cli]\ntheme = "neon"\n')], machine=True)
    assert console is not None
    out = capsys.readouterr().out
    assert '"level":"warn"' in out
    assert "Unknown CLI theme 'neon'" in out
