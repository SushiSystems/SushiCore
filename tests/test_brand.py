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

K_MARK_MAX_SIDE = 24
K_WORDMARK_MAX_WIDTH = 56
K_WORDMARK_MAX_ROWS = 16
K_WORDMARK_ROWS = 16
K_LETTER_HEIGHT = 7
K_LINE_STARTS = (0, 9)
K_LINE_LETTERS = (
    (("S", 6), ("U", 6), ("S", 6), ("H", 6), ("I", 2)),
    (("S", 6), ("Y", 6), ("S", 6), ("T", 6), ("E", 6), ("M", 8), ("S", 6)),
)
K_MIRRORED_LETTERS = ("U", "H", "I", "T", "Y", "M")


def _keys(grid: tuple[str, ...]) -> set[str]:
    """Return every character the grid uses."""
    return set("".join(grid))


def test_every_mark_row_has_the_same_width():
    assert len({len(row) for row in K_MARK_PIXELS}) == 1


def test_every_wordmark_row_has_the_same_width():
    assert len({len(row) for row in K_WORDMARK_PIXELS}) == 1


def test_the_mark_has_an_even_number_of_rows():
    assert len(K_MARK_PIXELS) % 2 == 0


def test_the_wordmark_has_an_even_number_of_rows():
    assert len(K_WORDMARK_PIXELS) % 2 == 0


def test_the_mark_stays_small_enough_for_a_help_screen():
    assert len(K_MARK_PIXELS) <= K_MARK_MAX_SIDE
    assert len(K_MARK_PIXELS[0]) <= K_MARK_MAX_SIDE


def _letters() -> list[tuple[str, tuple[str, ...]]]:
    """Return each letter of both wordmark lines with its rows, cut out by position."""
    letters = []
    for start, line in zip(K_LINE_STARTS, K_LINE_LETTERS):
        rows = K_WORDMARK_PIXELS[start : start + K_LETTER_HEIGHT]
        column = 0
        for name, width in line:
            letters.append((name, tuple(row[column : column + width] for row in rows)))
            column += width + 1
    return letters


def test_the_wordmark_has_sixteen_rows():
    assert len(K_WORDMARK_PIXELS) == K_WORDMARK_ROWS


def test_the_wordmark_stays_short_enough_to_sit_beside_the_mark():
    assert len(K_WORDMARK_PIXELS) <= K_WORDMARK_MAX_ROWS
    assert len(K_WORDMARK_PIXELS[0]) <= K_WORDMARK_MAX_WIDTH


def test_one_blank_column_separates_the_letters_and_two_blank_rows_the_lines():
    for start, line in zip(K_LINE_STARTS, K_LINE_LETTERS):
        rows = K_WORDMARK_PIXELS[start : start + K_LETTER_HEIGHT]
        column = 0
        for _, width in line[:-1]:
            column += width
            assert {row[column] for row in rows} == {K_TRANSPARENT}
            column += 1
    assert set("".join(K_WORDMARK_PIXELS[7:9])) == {K_TRANSPARENT}


@pytest.mark.parametrize("name", K_MIRRORED_LETTERS)
def test_these_letters_read_the_same_mirrored_left_to_right(name):
    found = [rows for letter, rows in _letters() if letter == name]
    assert found
    assert all(rows == tuple(row[::-1] for row in rows) for rows in found)


def test_the_s_reads_the_same_after_a_half_turn():
    found = [rows for letter, rows in _letters() if letter == "S"]
    assert len(found) == 5
    assert all(rows == tuple(row[::-1] for row in reversed(rows)) for rows in found)


def test_the_mark_uses_only_brand_keys_glow_keys_and_the_transparent_key():
    assert _keys(K_MARK_PIXELS) <= set(K_PALETTE) | set(K_GLOW_PALETTE) | {K_TRANSPARENT}


def test_the_wordmark_uses_only_the_foreground_key_amber_and_the_transparent_key():
    assert _keys(K_WORDMARK_PIXELS) <= {K_FOREGROUND_KEY, "a", K_TRANSPARENT}


def test_every_palette_key_appears_in_one_of_the_grids():
    drawn = _keys(K_MARK_PIXELS) | _keys(K_WORDMARK_PIXELS)
    assert set(K_PALETTE) | set(K_GLOW_PALETTE) <= drawn


def test_palette_values_are_lowercase_hex_colours():
    values = [*K_PALETTE.values(), *K_GLOW_PALETTE.values()]
    assert all(re.fullmatch(r"#[0-9a-f]{6}", value) for value in values)


def test_the_palette_names_the_four_brand_keys():
    assert set(K_PALETTE) == {"n", "r", "a", "g"}


def test_the_glow_palette_names_the_inner_and_outer_ring():
    assert set(K_GLOW_PALETTE) == {"h", "H"}


def test_the_foreground_key_is_not_a_palette_key():
    assert K_FOREGROUND_KEY not in set(K_PALETTE) | set(K_GLOW_PALETTE)
