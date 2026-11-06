# test_header.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""A header is a blank line and a titled rule."""

from rich.markup import escape

import pytest

from sushicore.ui.header import Header
from tests.ui.capture import capture, capture_ansi


pytestmark = pytest.mark.small


def test_header_is_a_blank_line_then_a_rule_holding_the_title():
    assert capture(Header("Setup"), width=20) == "\n────── Setup ───────\n"


@pytest.mark.parametrize(
    ("color_system", "code"), [("256", "38;5;"), ("truecolor", "38;2;240;165;0")], ids=["256", "truecolour"],
)
def test_the_header_is_drawn_in_the_colour_codes_of_the_terminal(color_system, code):
    assert code in capture_ansi(Header("Setup"), color_system=color_system)


def test_a_marked_up_title_prints_without_its_tags():
    text = capture(Header("[bold]Setup[/bold]"), width=20)
    assert "Setup" in text and "[bold]" not in text


def test_an_escaped_bracket_in_a_title_prints_literally():
    text = capture(Header(escape("Build [debug|release]")), width=40)
    assert "Build [debug|release]" in text


def test_the_theme_style_sits_under_the_markup_of_a_title():
    ansi = capture_ansi(Header("plain [italic]slanted[/italic]"), width=40)
    assert "\x1b[1;38;2;240;165;0mplain \x1b[0m" in ansi
    assert "\x1b[1;3;38;2;240;165;0mslanted\x1b[0m" in ansi
