# test_logo.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The logo draws the mark, the wordmark beside it and the glow behind it, in half blocks."""

from pathlib import Path

import pytest
from rich.console import Console
from rich.text import Text

from sushicore.brand import K_MARK_PIXELS
from sushicore.ui.logo import Logo
from tests.ui.capture import capture, capture_ansi


K_WIDE = 80
K_GOLDEN = Path(__file__).resolve().parent / "goldens" / "logo"
K_TINY_PALETTE = (("a", "#f0a500"), ("n", "#1d1e20"), ("g", "#4caf50"))


def _tiny(mark: tuple[str, ...], wordmark: tuple[str, ...] = (".", "."), **fields) -> Logo:
    """Return a logo drawn from grids and a palette small enough to read in an assertion."""
    return Logo(indent=0, mark_pixels=mark, wordmark_pixels=wordmark, palette=K_TINY_PALETTE, **fields)


def _lines(logo: Logo) -> list[str]:
    """Return the logo's plain rows, without the final empty split."""
    return capture(logo, width=K_WIDE).split("\n")[:-1]


def _cells(ansi: str) -> list[tuple[str, str]]:
    """Return each character of a terminal capture with the style it is drawn in."""
    segments = Text.from_ansi(ansi).render(Console(width=K_WIDE))
    return [(character, str(segment.style)) for segment in segments for character in segment.text]


@pytest.mark.small
@pytest.mark.parametrize(
    ("logo", "rows", "columns"),
    [
        (Logo(glow=True), 8, 72),
        (Logo(), 8, 68),
        (Logo(wordmark=False, glow=True), 8, 20),
        (Logo(wordmark=False), 6, 16),
        (Logo(indent=0, glow=True), len(K_MARK_PIXELS) // 2, 70),
    ],
    ids=["glowing lockup", "plain lockup", "glowing mark", "plain mark", "two pixel rows per row"],
)
def test_the_logo_takes_its_rows_and_columns(logo, rows, columns):
    lines = _lines(logo)
    assert (len(lines), logo.width, max(len(line) for line in lines) <= columns) == (rows, columns, True)


@pytest.mark.small
@pytest.mark.parametrize("glow", [False, True])
@pytest.mark.parametrize("wordmark", [False, True])
def test_the_widest_row_is_as_wide_as_the_width_says(wordmark, glow):
    logo = Logo(indent=0, wordmark=wordmark, glow=glow)
    assert max(len(line) for line in _lines(logo)) == logo.width


@pytest.mark.small
@pytest.mark.parametrize("wordmark", [False, True])
def test_the_plain_logo_has_no_blank_edge_row_or_column(wordmark):
    lines = _lines(Logo(indent=0, wordmark=wordmark))
    assert lines[0].strip() and lines[-1].strip()
    assert min(len(line) - len(line.lstrip()) for line in lines) == 0


@pytest.mark.small
def test_indent_prefixes_every_non_empty_row():
    lines = [line for line in capture(Logo(indent=3), width=K_WIDE).split("\n") if line]
    assert lines and all(line.startswith("   ") for line in lines)


@pytest.mark.small
def test_each_cell_picks_the_block_that_shows_its_two_pixels():
    assert capture(_tiny(("a.n..g", "a.a.g."), wordmark=False)).rstrip("\n") == "█ ▀ ▄▀"


@pytest.mark.small
def test_two_different_colours_share_one_cell_as_foreground_and_background():
    cell = "\x1b[38;2;29;30;32;48;2;240;165;0m▀\x1b[0m"
    assert cell in capture_ansi(_tiny(("a.n..g", "a.a.g."), wordmark=False))


@pytest.mark.small
def test_the_wordmark_sits_two_columns_after_the_mark():
    assert capture(_tiny(("a", "a"), ("n", "n"))).rstrip("\n") == "█  █"


@pytest.mark.small
def test_a_shorter_grid_is_centred_against_the_taller_one():
    assert capture(_tiny(("a", "a", "a", "a"), ("n", "n"))).split("\n")[:-1] == ["█  ▄", "█  ▀"]


@pytest.mark.small
@pytest.mark.parametrize(("glow", "lines"), [(False, ["█▀"]), (True, ["█▀▀█", "█▀▀█"])], ids=["plain", "glow"])
def test_transparent_edge_rows_and_columns_are_dropped_unless_the_glow_inks_them(glow, lines):
    logo = _tiny(("hhhh", "hnnh", "hnah", "hhhh"), wordmark=False, glow=glow)
    assert capture(logo).rstrip("\n").split("\n") == lines


@pytest.mark.small
def test_an_odd_trimmed_row_count_gains_one_transparent_row_at_the_bottom():
    logo = _tiny(("....", ".n..", ".a..", ".g..", "...."), wordmark=False)
    assert capture(logo).rstrip("\n").split("\n") == ["▀", "▀"]


@pytest.mark.small
@pytest.mark.parametrize(("glow", "width"), [(False, 2 + 2 + 1), (True, 4 + 2 + 1)], ids=["plain", "glow"])
def test_the_trimmed_mark_sets_the_width_beside_the_wordmark(glow, width):
    assert _tiny(("hhhh", "hnnh", "hnah", "hhhh"), ("n", "n"), glow=glow).width == width


@pytest.mark.small
def test_the_glow_rings_draw_nothing_until_the_glow_is_asked_for():
    assert capture(_tiny(("h.", ".H"), wordmark=False)).rstrip("\n") == ""


@pytest.mark.small
def test_the_glow_rings_draw_in_their_own_colours_when_asked():
    output = capture_ansi(_tiny(("h.", ".H"), wordmark=False, glow=True))
    assert ("\x1b[38;2;140;140;140m▀" in output, "\x1b[38;2;61;61;61m▄" in output) == (True, True)


@pytest.mark.small
def test_no_glow_colour_reaches_a_light_terminal():
    output = capture_ansi(Logo(), width=K_WIDE)
    assert "140;140;140" not in output
    assert "61;61;61" not in output


@pytest.mark.small
def test_only_the_wordmark_draws_in_the_terminal_foreground():
    assert "\x1b[39m" in capture_ansi(Logo(), width=K_WIDE)
    assert "\x1b[39m" not in capture_ansi(Logo(wordmark=False), width=K_WIDE)


@pytest.mark.medium
@pytest.mark.parametrize(
    ("logo", "golden"),
    [(Logo(), "logo_light_truecolor.txt"), (Logo(glow=True), "logo_dark_truecolor.txt")],
    ids=["light", "dark"],
)
def test_each_cell_of_the_logo_matches_its_golden_file(logo, golden):
    expected = (K_GOLDEN / golden).read_text(encoding="utf-8")
    assert _cells(capture_ansi(logo, width=K_WIDE)) == _cells(expected)


@pytest.mark.small
def test_width_matches_the_widest_row_when_the_wordmark_is_ragged():
    logo = Logo(indent=0, mark_pixels=("aa", "aa"), wordmark_pixels=("a", "aaaa"), palette=(("a", "#f0a500"),))
    rows = capture(logo, 80).split("\n")[:-1]
    assert logo.width == max(len(row) for row in rows)
