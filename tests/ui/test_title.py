"""A title is a name and, under it, a description."""

from sushicore.ui.title import Title
from tests.ui.capture import capture


def test_title_draws_the_name_then_the_description():
    assert capture(Title("hub", "One tree for the stack.")) == "hub\nOne tree for the stack.\n"


def test_title_without_a_description_is_the_name_alone():
    assert capture(Title("hub add")) == "hub add\n"


def test_description_interprets_rich_markup():
    title = Title("gui", "Builds into [cyan]build/hub[/cyan].")
    assert capture(title) == "gui\nBuilds into build/hub.\n"
