# Task 13 — the logo data and component

Wave 6a of `docs/agent/plans/2026-09-21-terminal-components.md`. `Logo` now has the public shape
Task 15 depends on: `Logo(indent=2, wordmark=True, glow=False)` with a `width` property.

## Files changed

| File | Change |
| --- | --- |
| `sushicore/brand.py` | Rewritten. `K_LOGO_PIXELS` is gone; `K_FOREGROUND_KEY`, `K_GLOW_PALETTE`, `K_MARK_PIXELS` and `K_WORDMARK_PIXELS` are new. Grids copied from the plan character for character. |
| `sushicore/ui/logo.py` | Rewritten. `indent`, `wordmark`, `glow`, a `width` property, and the module helpers `_colours`, `_centred`, `_pixels`, `_cell`. |
| `tests/test_brand.py` | Rewritten for the two grids and the two palettes, 13 tests. |
| `tests/ui/test_logo.py` | Rewritten, 15 tests. |
| `tests/golden/logo_light_truecolor.txt` | New. `capture_ansi(Logo(), width=80)`. |
| `tests/golden/logo_dark_truecolor.txt` | New. `capture_ansi(Logo(glow=True), width=80)`. |
| `tests/golden/logo_truecolor.txt` | Deleted. |

The owner approved the redesign in the Wave 6 introduction, so replacing the old golden with two
new ones is an approved golden update, not a regeneration to silence a failure. Both were written
once, from the implementation, by a throwaway script in the session scratchpad, as UTF-8 with
`\n` newlines.

## Design notes

Two things the plan left open:

`render` and `width` read `K_MARK_PIXELS`, `K_WORDMARK_PIXELS`, `K_PALETTE` and `K_GLOW_PALETTE`
through the module globals of `sushicore/ui/logo.py` at call time, never captured in a default
argument or a class attribute, so `monkeypatch.setattr("sushicore.ui.logo.K_MARK_PIXELS", ...)`
reaches them. Four tests rely on that with two-row grids.

Rich's style cache did not bite. `tests/conftest.py` from Task 16 had landed before I ran the full
suite, and the two golden tests pass both alone and inside `python -m pytest tests -q`.

`_colours(glow)` builds the key-to-colour map per render: the brand palette, the glow palette when
`glow` is true, and `"default"` for `K_FOREGROUND_KEY`. A key missing from the map is transparent,
so the two ring keys draw spaces when the glow is off. `_cell` takes that map as an argument and
keeps its five cases.

I did not monkeypatch `K_GLOW_PALETTE` in the glow tests, although the plan lists it: the escape
codes the plan names (`38;2;92;63;0` and `38;2;42;29;0`) are the real `#5c3f00` and `#2a1d00`, so
patching it to itself would add a line and prove nothing.

## Commands

Before the change, `python -m pytest tests/test_brand.py tests/ui/test_logo.py -q`:

```
tests\test_brand.py:5: in <module>
    from sushicore.brand import (
E   ImportError: cannot import name 'K_FOREGROUND_KEY' from 'sushicore.brand' (D:\Projects\sushicore\sushicore\brand.py)
___________________ ERROR collecting tests/ui/test_logo.py ____________________
ImportError while importing test module 'D:\Projects\sushicore\tests\ui\test_logo.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
C:\ProgramData\Miniconda\Lib\importlib\__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\ui\test_logo.py:5: in <module>
    from sushicore.brand import K_MARK_PIXELS
E   ImportError: cannot import name 'K_MARK_PIXELS' from 'sushicore.brand' (D:\Projects\sushicore\sushicore\brand.py)
=========================== short test summary info ===========================
ERROR tests/test_brand.py
ERROR tests/ui/test_logo.py
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!
2 errors in 0.11s
```

After the change,
`python -m pytest tests/test_brand.py tests/ui/test_logo.py tests/test_ui_architecture.py -v`:

```
============================= test session starts =============================
platform win32 -- Python 3.13.13, pytest-9.1.1, pluggy-1.6.0 -- C:\ProgramData\Miniconda\python.exe
cachedir: .pytest_cache
rootdir: D:\Projects\sushicore
configfile: pyproject.toml
plugins: anyio-4.12.1
collecting ... collected 71 items

tests/test_brand.py::test_every_mark_row_has_the_same_width PASSED       [  1%]
tests/test_brand.py::test_every_wordmark_row_has_the_same_width PASSED   [  2%]
tests/test_brand.py::test_the_mark_has_an_even_number_of_rows PASSED     [  4%]
tests/test_brand.py::test_the_wordmark_has_an_even_number_of_rows PASSED [  5%]
tests/test_brand.py::test_the_mark_stays_small_enough_for_a_help_screen PASSED [  7%]
tests/test_brand.py::test_the_wordmark_stays_short_enough_to_sit_beside_the_mark PASSED [  8%]
tests/test_brand.py::test_the_mark_uses_only_brand_keys_glow_keys_and_the_transparent_key PASSED [  9%]
tests/test_brand.py::test_the_wordmark_uses_only_the_foreground_key_amber_and_the_transparent_key PASSED [ 11%]
tests/test_brand.py::test_every_palette_key_appears_in_one_of_the_grids PASSED [ 12%]
tests/test_brand.py::test_palette_values_are_lowercase_hex_colours PASSED [ 14%]
tests/test_brand.py::test_the_palette_names_the_four_brand_keys PASSED   [ 15%]
tests/test_brand.py::test_the_glow_palette_names_the_inner_and_outer_ring PASSED [ 16%]
tests/test_brand.py::test_the_foreground_key_is_not_a_palette_key PASSED [ 18%]
tests/ui/test_logo.py::test_two_pixel_rows_become_one_terminal_row PASSED [ 19%]
tests/ui/test_logo.py::test_the_lockup_is_eight_rows_and_sixty_five_columns PASSED [ 21%]
tests/ui/test_logo.py::test_the_mark_alone_stays_inside_twenty_columns PASSED [ 22%]
tests/ui/test_logo.py::test_width_counts_the_indent PASSED               [ 23%]
tests/ui/test_logo.py::test_indent_prefixes_every_non_empty_row PASSED   [ 25%]
tests/ui/test_logo.py::test_each_cell_picks_the_block_that_shows_its_two_pixels PASSED [ 26%]
tests/ui/test_logo.py::test_two_different_colours_share_one_cell_as_foreground_and_background PASSED [ 28%]
tests/ui/test_logo.py::test_the_wordmark_sits_two_columns_after_the_mark PASSED [ 29%]
tests/ui/test_logo.py::test_a_shorter_grid_is_centred_against_the_taller_one PASSED [ 30%]
tests/ui/test_logo.py::test_the_glow_rings_draw_nothing_until_the_glow_is_asked_for PASSED [ 32%]
tests/ui/test_logo.py::test_the_glow_rings_draw_in_their_own_colours_when_asked PASSED [ 33%]
tests/ui/test_logo.py::test_no_glow_colour_reaches_a_light_terminal PASSED [ 35%]
tests/ui/test_logo.py::test_only_the_wordmark_draws_in_the_terminal_foreground PASSED [ 36%]
tests/ui/test_logo.py::test_the_light_logo_matches_its_golden_file PASSED [ 38%]
```

The same run's last lines:

```
tests/test_ui_architecture.py::test_file_imports_only_what_a_component_may[usage.py] PASSED [100%]

============================= 71 passed in 0.16s ==============================
```

`python -m pytest tests -q`:

```
........................................................................ [ 25%]
........................................................................ [ 50%]
........................................................................ [ 76%]
...................................................................      [100%]
283 passed in 0.79s
```

`python -m py_compile sushicore/brand.py sushicore/ui/logo.py tests/test_brand.py tests/ui/test_logo.py; echo "exit $?"`:

```
exit 0
```

## The shape

`Logo(indent=0)`, printed plain at 80 columns under `PYTHONIOENCODING=utf-8`:

```
                     ▄▄▄▄ ▄▄ ▄▄  ▄▄▄▄ ▄▄ ▄▄ ▄▄
   ▄▄▀▀▀▀▀▀██▄      ▀█▄▄  ██ ██ ▀█▄▄  ██▄██ ██
  ▄██▀▀▀▀▀██▀██        ██ ██ ██    ██ ██▀██ ██
  █████████▀████    ▀▀▀▀   ▀▀▀  ▀▀▀▀  ▀▀ ▀▀ ▀▀
  ██████████████     ▄▄▄▄ ▄▄ ▄▄  ▄▄▄▄ ▄▄▄▄▄ ▄▄▄▄▄ ▄▄▄ ▄▄▄  ▄▄▄▄
  ███▀▀██▀▀████▀    ▀█▄▄  ▀█▄█▀ ▀█▄▄    █   ██▄▄  ███████ ▀█▄▄
   ▀▀▀▀▀▀▀▀▀▀▀         ██   █      ██   █   ██    ██ ▀ ██    ██
                    ▀▀▀▀    ▀   ▀▀▀▀    ▀   ▀▀▀▀▀ ▀▀   ▀▀ ▀▀▀▀
```

`Logo(indent=0, wordmark=False)`:

```

   ▄▄▀▀▀▀▀▀██▄
  ▄██▀▀▀▀▀██▀██
  █████████▀████
  ██████████████
  ███▀▀██▀▀████▀
   ▀▀▀▀▀▀▀▀▀▀▀
```

Both are the no-colour capture, so the glow ring is absent and the roll's nori, rice, amber and
green all print as the same block. The first row of the mark-only shape is blank because the
mark's top two pixel rows hold only ring pixels.

## Not done

I did not touch `sushicore/help/page.py` or `sushicore/typer_help.py`, which still pass
`show_logo` and get `Logo()`'s new defaults. Task 15 rewires them. Nothing in `tests/help/` or
`tests/test_typer_help.py` failed because of it.

I did not commit, and did not edit `pyproject.toml`, `README.md`, `docs/README.md`,
`docs/reference/CHANGELOG.md`, any spec or plan, or any `__init__.py`. `sushicore/ui/__init__.py`
re-exports `Logo`, which needs no change.

The rendered lockup has not been checked on a real dark terminal with the glow on; the
`logo_dark_truecolor.txt` golden is the only evidence for it, and the owner's eye at the Wave 6
review would settle whether the two ring colours read as a back-light.
