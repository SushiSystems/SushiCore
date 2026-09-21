"""choose_logo picks the widest logo a console has room for."""

import pytest

from sushicore.help.logo_choice import choose_logo
from sushicore.ui.logo import Logo


@pytest.mark.parametrize("dark", [False, True])
def test_a_console_as_wide_as_the_lockup_gets_the_mark_and_the_wordmark(dark):
    logo = choose_logo(width=Logo(glow=dark).width, dark_background=dark)
    assert logo is not None and logo.wordmark


@pytest.mark.parametrize("dark", [False, True])
def test_one_column_short_of_the_lockup_drops_the_wordmark(dark):
    logo = choose_logo(width=Logo(glow=dark).width - 1, dark_background=dark)
    assert logo is not None and not logo.wordmark


@pytest.mark.parametrize("dark", [False, True])
def test_a_console_as_wide_as_the_mark_gets_the_mark_alone(dark):
    mark = Logo(wordmark=False, glow=dark)
    assert choose_logo(width=mark.width, dark_background=dark) == mark


@pytest.mark.parametrize("dark", [False, True])
def test_one_column_short_of_the_mark_gets_nothing(dark):
    width = Logo(wordmark=False, glow=dark).width - 1
    assert choose_logo(width=width, dark_background=dark) is None


@pytest.mark.parametrize("dark", [False, True])
def test_the_glow_follows_the_background(dark):
    lockup = choose_logo(width=Logo(glow=dark).width, dark_background=dark)
    mark = choose_logo(width=Logo(wordmark=False, glow=dark).width, dark_background=dark)
    assert lockup is not None and mark is not None
    assert lockup.glow is dark and mark.glow is dark


def test_a_console_of_no_width_gets_nothing():
    assert choose_logo(width=0, dark_background=True) is None
