# test_brand.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The mark and the wordmark are well-formed pixel grids over the brand palettes."""

import re

import pytest

from sushicore.brand import (
    K_FOREGROUND_KEY,
    K_GLOW_PALETTE,
    K_MARK_PIXELS,
    K_PALETTE,
    K_TRANSPARENT,
    K_WORDMARK_PIXELS,
)


pytestmark = pytest.mark.small


def _keys(grid: tuple[str, ...]) -> set[str]:
    """Return every character the grid uses."""
    return set("".join(grid))


def test_every_mark_row_has_the_same_width():
    assert len({len(row) for row in K_MARK_PIXELS}) == 1


def test_every_wordmark_row_has_the_same_width():
    assert len({len(row) for row in K_WORDMARK_PIXELS}) == 1


def test_the_mark_uses_only_brand_keys_glow_keys_and_the_transparent_key():
    assert _keys(K_MARK_PIXELS) <= set(K_PALETTE) | set(K_GLOW_PALETTE) | {K_TRANSPARENT}


def test_the_wordmark_uses_only_the_foreground_key_amber_and_the_transparent_key():
    assert _keys(K_WORDMARK_PIXELS) <= {K_FOREGROUND_KEY, "a", K_TRANSPARENT}


def test_palette_values_are_lowercase_hex_colours():
    values = [*K_PALETTE.values(), *K_GLOW_PALETTE.values()]
    assert all(re.fullmatch(r"#[0-9a-f]{6}", value) for value in values)


def test_the_foreground_key_is_not_a_palette_key():
    assert K_FOREGROUND_KEY not in set(K_PALETTE) | set(K_GLOW_PALETTE)
