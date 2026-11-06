# test_logo_choice.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""choose_logo picks the widest logo a console has room for."""

import pytest

from sushicore.help.logo_choice import choose_logo
from sushicore.ui.logo import Logo


pytestmark = pytest.mark.small


K_LOCKUP = "the mark and the wordmark"
K_MARK = "the mark alone"


@pytest.mark.parametrize("dark", [False, True])
@pytest.mark.parametrize(
    ("width_of", "expected"),
    [
        (lambda lockup, mark: lockup, K_LOCKUP),
        (lambda lockup, mark: lockup - 1, K_MARK),
        (lambda lockup, mark: mark, K_MARK),
        (lambda lockup, mark: mark - 1, None),
        (lambda lockup, mark: 0, None),
    ],
    ids=["as wide as the lockup", "one short of the lockup", "as wide as the mark",
         "one short of the mark", "no width"],
)
def test_a_console_gets_the_widest_logo_it_has_room_for(dark, width_of, expected):
    lockup, mark = Logo(glow=dark), Logo(wordmark=False, glow=dark)
    chosen = choose_logo(width=width_of(lockup.width, mark.width), dark_background=dark)
    names = {lockup: K_LOCKUP, mark: K_MARK}
    assert names.get(chosen) == expected


@pytest.mark.parametrize("dark", [False, True])
def test_the_glow_follows_the_background(dark):
    lockup = choose_logo(width=Logo(glow=dark).width, dark_background=dark)
    mark = choose_logo(width=Logo(wordmark=False, glow=dark).width, dark_background=dark)
    assert lockup is not None and mark is not None
    assert lockup.glow is dark and mark.glow is dark
