"""A title is a name and, under it, a description."""

from rich.color import ColorSystem
from rich.style import Style

from sushicore.ui.title import Title
from tests.ui.capture import capture, capture_ansi


def _painted(style: str, text: str) -> str:
    """Return ``text`` as a truecolour terminal shows it in ``style``."""
    return Style.parse(style).render(text, color_system=ColorSystem.TRUECOLOR)


def test_title_draws_the_name_then_the_description():
    assert capture(Title("hub", "One tree for the stack.")) == "hub\nOne tree for the stack.\n"


def test_title_without_a_description_is_the_name_alone():
    assert capture(Title("hub add")) == "hub add\n"


def test_description_interprets_rich_markup():
    title = Title("gui", "Builds into [cyan]build/hub[/cyan].")
    assert capture(title) == "gui\nBuilds into build/hub.\n"


def test_a_bracket_that_names_a_style_still_styles_its_text():
    assert _painted("cyan", "build/hub") in capture_ansi(
        Title("gui", "Builds into [cyan]build/hub[/cyan].")
    )


def test_an_unescaped_extra_marker_stays_in_the_description():
    title = Title("hub add", "Bring a module in.  [required]")
    assert capture(title) == "hub add\nBring a module in.  [required]\n"


def test_an_escaped_extra_marker_shows_its_brackets_once():
    assert capture(Title("hub", "Kind.  \\[default: debug]")) == "hub\nKind.  [default: debug]\n"


def test_a_theme_style_name_in_the_description_is_still_a_tag():
    assert capture(Title("hub", "Say [success]yes[/success].")) == "hub\nSay yes.\n"
