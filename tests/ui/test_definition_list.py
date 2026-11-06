# test_definition_list.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""A definition list is a heading over a term column and a text column."""

from rich.color import ColorSystem
from rich.style import Style

import pytest

from sushicore.theme import Theme, get_theme
from sushicore.ui.definition_list import DefinitionList
from tests.ui.capture import capture, capture_ansi, capture_raw


pytestmark = pytest.mark.small

K_BOLD_AMBER = "[1;38;2;240;165;0m"
K_AMBER = "[38;2;240;165;0m"
K_BOLD = "[1m"


def _painted(style: str, text: str) -> str:
    """Return ``text`` as a truecolour terminal shows it in ``style``."""
    return Style.parse(style).render(text, color_system=ColorSystem.TRUECOLOR)


def test_entries_align_and_the_text_wraps_inside_its_column():
    entries = (
        ("add", "Bring one or more stack modules into the workspace, with what they need."),
        ("install-cli", "Install a [cyan]module[/cyan]'s CLI."),
    )
    assert capture(DefinitionList("Modules", entries), width=50) == (
        "Modules\n"
        "  add          Bring one or more stack modules\n"
        "               into the workspace, with what they\n"
        "               need.\n"
        "  install-cli  Install a module's CLI.\n"
    )


def test_a_term_with_brackets_is_printed_literally():
    text = capture(DefinitionList("Options", (("--type [debug|release]", "The build type."),)))
    assert "--type [debug|release]" in text


def test_an_entry_without_text_prints_its_term_alone():
    assert capture(DefinitionList("Examples", (("hub doctor", ""),))) == "Examples\n  hub doctor\n"


def test_a_bracket_that_names_a_style_still_styles_its_text():
    entries = (("--kind", "Paint [cyan]x[/cyan]."),)
    assert "Paint x." in capture(DefinitionList("Options", entries))
    assert _painted("cyan", "x") in capture_ansi(DefinitionList("Options", entries))


def test_a_theme_style_name_in_the_text_is_still_a_tag():
    entries = (("--kind", "Say [success]yes[/success]."),)
    assert "Say yes." in capture(DefinitionList("Options", entries))


def test_a_row_is_not_padded_to_the_console_width():
    entries = (("add", "Bring a module in."), ("install-cli", "Install a module's CLI."))
    lines = capture_raw(DefinitionList("Modules", entries), width=200).splitlines()
    assert max(len(line) for line in lines) <= 60


def _drawn(theme: Theme) -> str:
    """Return a one-entry list under the heading Modules as a truecolour terminal shows it."""
    return capture_ansi(DefinitionList("Modules", (("add", "Bring."),)), theme=theme)


@pytest.mark.parametrize(
    ("theme", "heading"),
    [(Theme(), _painted(Theme().header, "Modules")), (get_theme("default"), f"{K_BOLD_AMBER}Modules"),
     (get_theme("mono"), f"{K_BOLD}Modules")],
    ids=["built-in", "sushiweb", "mono"],
)
def test_the_heading_is_drawn_bold_in_the_theme_header_style(theme, heading):
    assert heading in _drawn(theme)


@pytest.mark.parametrize(
    ("theme", "term", "not_term"),
    [
        (Theme(), _painted(Theme().cmd, "add"), _painted(f"bold {Theme().cmd}", "add")),
        (get_theme("default"), f"{K_AMBER}add", f"{K_BOLD_AMBER}add"),
        (get_theme("mono"), "add", f"{K_BOLD}add"),
        (get_theme("muted"), _painted(get_theme("muted").cmd, "add"), f"{K_BOLD}add"),
    ],
    ids=["built-in", "sushiweb", "mono", "muted"],
)
def test_the_term_takes_the_theme_command_style_without_bold(theme, term, not_term):
    out = _drawn(theme)
    assert term in out and not_term not in out
