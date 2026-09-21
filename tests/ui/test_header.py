"""A header is a blank line and a titled rule."""

from rich.markup import escape

from sushicore.ui.header import Header
from tests.ui.capture import capture, capture_ansi


def test_header_is_a_blank_line_then_a_rule_holding_the_title():
    assert capture(Header("Setup"), width=20) == "\n────── Setup ───────\n"


def test_a_256_colour_render_can_run_before_the_truecolour_one():
    """Render at 256 colours, the first half of the pair below."""
    assert "38;5;" in capture_ansi(Header("Setup"), color_system="256")


def test_a_truecolour_render_keeps_its_codes_after_a_256_colour_one():
    """Render at truecolour right after the test above, which must leave nothing behind."""
    assert "38;2;240;165;0" in capture_ansi(Header("Setup"))


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
