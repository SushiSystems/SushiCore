# test_theme.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The muted token and the theme lookup."""

import pytest

from sushicore.errors import ConfigError
from sushicore.theme import Theme, get_theme, known_themes


pytestmark = pytest.mark.small


def test_muted_reaches_the_rich_style_map():
    assert Theme(muted="italic").as_rich_styles()["muted"] == "italic"


def test_muted_is_overridable_like_every_other_token():
    assert Theme().merged({"muted": "grey50"}).muted == "grey50"


def test_an_unknown_theme_name_raises_a_config_error_naming_the_known_themes():
    """get_theme of an unknown name raises ConfigError that lists the known themes."""
    with pytest.raises(ConfigError, match="Unknown CLI theme 'no-such-theme'.*" + known_themes()[0]):
        get_theme("no-such-theme")
