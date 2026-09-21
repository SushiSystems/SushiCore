"""The background setting travels from a TOML file and the environment to the console."""

import io

import pytest

from sushicore import build_console
from sushicore.config import load_appearance
from sushicore.console import Console
from sushicore.icons import IconSet
from sushicore.renderer import PlainRenderer
from sushicore.theme import Theme


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
