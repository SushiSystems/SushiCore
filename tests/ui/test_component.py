# test_component.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The Component protocol accepts anything that draws itself from a theme."""

from rich.text import Text

import pytest

from sushicore.theme import Theme
from sushicore.ui.component import Component


pytestmark = pytest.mark.small


class _Hello:
    """Draws one word, ignoring the theme it is handed."""

    def render(self, theme: Theme) -> Text:
        return Text("hello")


@pytest.mark.parametrize(
    ("candidate", "satisfies"), [(_Hello(), True), (object(), False)], ids=["with render", "without"],
)
def test_only_a_class_with_render_satisfies_the_protocol(candidate, satisfies):
    assert isinstance(candidate, Component) is satisfies
