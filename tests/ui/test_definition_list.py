"""A definition list is a heading over a term column and a text column."""

from rich.color import ColorSystem
from rich.style import Style

from sushicore.theme import Theme, get_theme
from sushicore.ui.definition_list import DefinitionList
from tests.ui.capture import capture, capture_ansi, capture_raw

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


def test_a_row_is_not_padded_to_the_console_width():
    entries = (("add", "Bring a module in."), ("install-cli", "Install a module's CLI."))
    lines = capture_raw(DefinitionList("Modules", entries), width=200).splitlines()
    assert max(len(line) for line in lines) <= 60


def test_the_heading_is_bold_and_the_term_carries_no_bold_in_the_default_theme():
    theme = Theme()
    out = capture_ansi(DefinitionList("Modules", (("add", "Bring."),)), theme=theme)
    assert _painted(theme.header, "Modules") in out
    assert _painted(theme.cmd, "add") in out
    assert _painted(f"bold {theme.cmd}", "add") not in out


def test_a_term_is_amber_and_a_heading_bold_amber_in_the_sushiweb_theme():
    out = capture_ansi(
        DefinitionList("Modules", (("add", "Bring."),)), theme=get_theme("default")
    )
    assert f"{K_BOLD_AMBER}Modules" in out
    assert f"{K_AMBER}add" in out
    assert f"{K_BOLD_AMBER}add" not in out


def test_a_term_is_plain_and_a_heading_bold_when_the_theme_command_style_is_only_bold():
    out = capture_ansi(
        DefinitionList("Modules", (("add", "Bring."),)), theme=get_theme("mono")
    )
    assert f"{K_BOLD}Modules" in out
    assert "add" in out and f"{K_BOLD}add" not in out


def test_a_theme_whose_command_style_is_not_bold_keeps_its_term_style():
    theme = get_theme("muted")
    out = capture_ansi(DefinitionList("Modules", (("add", "Bring."),)), theme=theme)
    assert _painted(theme.cmd, "add") in out
