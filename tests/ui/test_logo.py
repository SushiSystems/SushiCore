"""The logo draws the mark, the wordmark beside it and the glow behind it, in half blocks."""

from pathlib import Path

import pytest

from sushicore.brand import K_MARK_PIXELS
from sushicore.ui.logo import Logo
from tests.ui.capture import capture, capture_ansi

K_WIDE = 80
K_GOLDEN = Path(__file__).resolve().parents[1] / "golden"
K_TINY_PALETTE = {"a": "#f0a500", "n": "#1d1e20", "g": "#4caf50"}


def _tiny(monkeypatch, mark: tuple[str, ...], wordmark: tuple[str, ...] = (".", ".")) -> None:
    """Replace the grids and the brand palette with ones small enough to read in an assertion."""
    monkeypatch.setattr("sushicore.ui.logo.K_MARK_PIXELS", mark)
    monkeypatch.setattr("sushicore.ui.logo.K_WORDMARK_PIXELS", wordmark)
    monkeypatch.setattr("sushicore.ui.logo.K_PALETTE", K_TINY_PALETTE)


def _lines(logo: Logo) -> list[str]:
    """Return the logo's plain rows, without the final empty split."""
    return capture(logo, width=K_WIDE).split("\n")[:-1]


def test_two_pixel_rows_become_one_terminal_row():
    assert len(_lines(Logo(indent=0, glow=True))) == len(K_MARK_PIXELS) // 2


def test_the_glowing_lockup_is_eight_rows_and_seventy_two_columns():
    assert Logo(glow=True).width == 72
    assert len(_lines(Logo(glow=True))) == 8


def test_the_plain_lockup_is_eight_rows_and_sixty_eight_columns():
    assert Logo().width == 68
    assert len(_lines(Logo())) == 8


def test_the_glowing_mark_alone_stays_inside_twenty_columns():
    logo = Logo(wordmark=False, glow=True)
    assert logo.width == 20
    assert len(_lines(logo)) == 8
    assert all(len(line) <= 20 for line in _lines(logo))


def test_the_plain_mark_alone_is_six_rows_and_sixteen_columns():
    logo = Logo(wordmark=False)
    assert logo.width == 16
    assert len(_lines(logo)) == 6
    assert all(len(line) <= 16 for line in _lines(logo))


def test_width_counts_the_indent():
    assert Logo(indent=0).width == 66
    assert Logo(indent=0, glow=True).width == 70


@pytest.mark.parametrize("glow", [False, True])
@pytest.mark.parametrize("wordmark", [False, True])
def test_the_widest_row_is_as_wide_as_the_width_says(wordmark, glow):
    logo = Logo(indent=0, wordmark=wordmark, glow=glow)
    assert max(len(line) for line in _lines(logo)) == logo.width


@pytest.mark.parametrize("wordmark", [False, True])
def test_the_plain_logo_has_no_blank_edge_row_or_column(wordmark):
    lines = _lines(Logo(indent=0, wordmark=wordmark))
    assert lines[0].strip() and lines[-1].strip()
    assert min(len(line) - len(line.lstrip()) for line in lines) == 0


def test_the_plain_mark_alone_has_no_blank_first_line():
    assert _lines(Logo(indent=0, wordmark=False))[0].strip()


def test_indent_prefixes_every_non_empty_row():
    lines = [line for line in capture(Logo(indent=3), width=K_WIDE).split("\n") if line]
    assert lines and all(line.startswith("   ") for line in lines)


def test_each_cell_picks_the_block_that_shows_its_two_pixels(monkeypatch):
    _tiny(monkeypatch, ("a.n..g", "a.a.g."))
    assert capture(Logo(indent=0, wordmark=False)).rstrip("\n") == "█ ▀ ▄▀"


def test_two_different_colours_share_one_cell_as_foreground_and_background(monkeypatch):
    _tiny(monkeypatch, ("a.n..g", "a.a.g."))
    cell = "\x1b[38;2;29;30;32;48;2;240;165;0m▀\x1b[0m"
    assert cell in capture_ansi(Logo(indent=0, wordmark=False))


def test_the_wordmark_sits_two_columns_after_the_mark(monkeypatch):
    _tiny(monkeypatch, ("a", "a"), ("n", "n"))
    assert capture(Logo(indent=0)).rstrip("\n") == "█  █"


def test_a_shorter_grid_is_centred_against_the_taller_one(monkeypatch):
    _tiny(monkeypatch, ("a", "a", "a", "a"), ("n", "n"))
    assert capture(Logo(indent=0)).split("\n")[:-1] == ["█  ▄", "█  ▀"]


def test_transparent_edge_rows_and_columns_are_dropped_without_the_glow(monkeypatch):
    _tiny(monkeypatch, ("hhhh", "hnnh", "hnah", "hhhh"))
    assert capture(Logo(indent=0, wordmark=False)).rstrip("\n") == "█▀"


def test_the_same_edges_stay_with_the_glow(monkeypatch):
    _tiny(monkeypatch, ("hhhh", "hnnh", "hnah", "hhhh"))
    lines = capture(Logo(indent=0, wordmark=False, glow=True)).rstrip("\n").split("\n")
    assert lines == ["█▀▀█", "█▀▀█"]


def test_an_odd_trimmed_row_count_gains_one_transparent_row_at_the_bottom(monkeypatch):
    _tiny(monkeypatch, ("....", ".n..", ".a..", ".g..", "...."))
    lines = capture(Logo(indent=0, wordmark=False)).rstrip("\n").split("\n")
    assert lines == ["▀", "▀"]


def test_the_trimmed_mark_sets_the_width_beside_the_wordmark(monkeypatch):
    _tiny(monkeypatch, ("hhhh", "hnnh", "hnah", "hhhh"), ("n", "n"))
    assert Logo(indent=0).width == 2 + 2 + 1
    assert Logo(indent=0, glow=True).width == 4 + 2 + 1


def test_the_glow_rings_draw_nothing_until_the_glow_is_asked_for(monkeypatch):
    _tiny(monkeypatch, ("h.", ".H"))
    assert capture(Logo(indent=0, wordmark=False)).rstrip("\n") == ""


def test_the_glow_rings_draw_in_their_own_colours_when_asked(monkeypatch):
    _tiny(monkeypatch, ("h.", ".H"))
    output = capture_ansi(Logo(indent=0, wordmark=False, glow=True))
    assert "\x1b[38;2;140;140;140m▀" in output
    assert "\x1b[38;2;61;61;61m▄" in output


def test_no_glow_colour_reaches_a_light_terminal():
    output = capture_ansi(Logo(), width=K_WIDE)
    assert "140;140;140" not in output
    assert "61;61;61" not in output


def test_only_the_wordmark_draws_in_the_terminal_foreground():
    assert "\x1b[39m" in capture_ansi(Logo(), width=K_WIDE)
    assert "\x1b[39m" not in capture_ansi(Logo(wordmark=False), width=K_WIDE)


def test_the_light_logo_matches_its_golden_file():
    golden = (K_GOLDEN / "logo_light_truecolor.txt").read_text(encoding="utf-8")
    assert capture_ansi(Logo(), width=K_WIDE) == golden


def test_the_dark_logo_matches_its_golden_file():
    golden = (K_GOLDEN / "logo_dark_truecolor.txt").read_text(encoding="utf-8")
    assert capture_ansi(Logo(glow=True), width=K_WIDE) == golden
