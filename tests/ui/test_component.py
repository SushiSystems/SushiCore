"""The Component protocol accepts anything that draws itself from a theme."""

from rich.text import Text

from sushicore.theme import Theme
from sushicore.ui.component import Component


class _Hello:
    """Draws one word, ignoring the theme it is handed."""

    def render(self, theme: Theme) -> Text:
        return Text("hello")


def test_a_class_with_render_satisfies_the_protocol():
    assert isinstance(_Hello(), Component)


def test_a_class_without_render_does_not():
    assert not isinstance(object(), Component)
