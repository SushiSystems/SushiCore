"""The muted token and the console's public theme."""

import io

from sushicore.console import Console
from sushicore.icons import IconSet
from sushicore.renderer import PlainRenderer
from sushicore.theme import Theme


def test_muted_defaults_to_dim():
    assert Theme().muted == "dim"


def test_muted_reaches_the_rich_style_map():
    assert Theme(muted="italic").as_rich_styles()["muted"] == "italic"


def test_muted_is_overridable_like_every_other_token():
    assert Theme().merged({"muted": "grey50"}).muted == "grey50"


def test_console_exposes_the_theme_it_was_built_with():
    theme = Theme(muted="grey50")
    console = Console(PlainRenderer(stream=io.StringIO()), theme, IconSet())
    assert console.theme is theme
