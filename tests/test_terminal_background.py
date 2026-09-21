"""The background decision reads a setting first and COLORFGBG only when asked to."""

import pytest

from sushicore.terminal_background import is_dark_background


def test_dark_wins_over_a_light_colorfgbg():
    assert is_dark_background("dark", {"COLORFGBG": "0;15"})


def test_light_wins_over_a_dark_colorfgbg():
    assert not is_dark_background("light", {"COLORFGBG": "15;0"})


@pytest.mark.parametrize("value", ["15;0", "15;default;0", "7;6", "7;8"])
def test_auto_reads_a_dark_background_index(value):
    assert is_dark_background("auto", {"COLORFGBG": value})


@pytest.mark.parametrize("value", ["0;15", "0;7", "15;9", "", "garbage", "15;-1"])
def test_auto_reads_anything_else_as_not_dark(value):
    assert not is_dark_background("auto", {"COLORFGBG": value})


def test_auto_without_the_variable_is_not_dark():
    assert not is_dark_background("auto", {})
