"""A bracket is markup only when what it names is a style; every other one stays text."""

import pytest
from rich.text import Text

from sushicore.markup import escape_unknown_tags

K_THEME_NAMES = {"success": "bold green", "error": "bold red", "cmd": "cyan"}


def _escape(text: str, known: dict[str, str] | None = None) -> str:
    """Return ``text`` escaped against the theme names, or against ``known`` when given."""
    return escape_unknown_tags(text, K_THEME_NAMES if known is None else known)


def _shown(text: str) -> str:
    """Return the plain text Rich draws for ``text`` after it has been escaped."""
    return Text.from_markup(_escape(text)).plain


def test_a_bracket_that_names_no_style_is_escaped():
    assert _escape("hdf5[core,zlib]") == r"hdf5\[core,zlib]"


def test_a_cell_with_a_feature_list_survives_a_round_trip_through_markup():
    cell = "Dear ImGui (imgui[glfw-binding,opengl3-binding])"
    assert _shown(cell) == cell


@pytest.mark.parametrize("text", ["[red]x[/red]", "[bold red]x[/]", "[on blue]x[/on blue]"])
def test_a_bracket_that_names_a_rich_style_is_left_alone(text):
    assert _escape(text) == text


def test_a_theme_name_is_left_alone_when_it_is_known():
    assert _escape("[success]ok[/success]") == "[success]ok[/success]"


def test_a_theme_name_is_escaped_when_it_is_not_known_and_not_a_rich_style():
    assert _escape("[success]ok[/success]", known={}) == r"\[success]ok\[/success]"


def test_the_bare_close_everything_tag_is_left_alone():
    assert _escape("[/]") == "[/]"


def test_a_bracket_that_is_already_escaped_is_left_alone():
    assert _escape(r"hdf5\[core,zlib]") == r"hdf5\[core,zlib]"


def test_several_brackets_in_one_string_are_judged_one_by_one():
    text = "[error]hdf5[core,zlib][/error] and [cmd]x[/cmd] [not,a,style]"
    assert _escape(text) == r"[error]hdf5\[core,zlib][/error] and [cmd]x[/cmd] \[not,a,style]"


def test_a_string_without_brackets_is_returned_unchanged():
    assert _escape("plain text (1 of 2)") == "plain text (1 of 2)"


def test_a_link_stays_a_link():
    text = "[link=https://example.com]x[/link]"
    assert _escape(text) == text
    assert Text.from_markup(_escape(text)).spans[0].style == "link https://example.com"


def test_a_link_written_with_a_space_stays_a_link_when_closed_with_a_bare_slash():
    text = "[link https://example.com]x[/]"
    assert _escape(text) == text


def test_a_closing_tag_that_closes_nothing_and_names_no_style_is_escaped():
    assert _escape("x[/link]") == r"x\[/link]"


def test_a_closing_tag_is_matched_against_the_opening_tag_it_follows():
    text = "[link=https://example.com]a[/link] b[/link]"
    assert _escape(text) == "[link=https://example.com]a[/link] b\\[/link]"


@pytest.mark.parametrize("name", ["0", "1;2", " x "])
def test_a_numeric_or_oddly_spelled_name_is_not_a_style(name):
    assert _escape(f"a[{name}]b") == f"a\\[{name}]b"
    assert _shown(f"a[{name}]b") == f"a[{name}]b"


@pytest.mark.parametrize("name", ["", " "])
def test_an_empty_name_is_left_alone(name):
    assert _escape(f"a[{name}]b") == f"a[{name}]b"
    assert _shown(f"a[{name}]b") == f"a[{name}]b"


def test_a_bracket_after_an_even_run_of_backslashes_is_not_escaped():
    assert _escape("\\\\[core,zlib]") == "\\\\\\[core,zlib]"


def test_a_bracket_after_an_odd_run_of_backslashes_is_escaped_already():
    assert _escape("\\\\\\[core,zlib]") == "\\\\\\[core,zlib]"


def test_a_key_value_bracket_is_not_a_style():
    assert _shown("pkg[feature=on]") == "pkg[feature=on]"


def test_a_styled_cell_keeps_its_style_and_loses_only_its_tags():
    text = Text.from_markup(_escape("[error]FAIL[/error] hdf5[core]"))
    assert text.plain == "FAIL hdf5[core]"
    assert [(span.start, span.end, span.style) for span in text.spans] == [(0, 4, "error")]
