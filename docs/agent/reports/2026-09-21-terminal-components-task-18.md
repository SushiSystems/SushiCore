# Task 18 report: a larger, symmetric wordmark and a white glow

## Files changed

- `sushicore/brand.py`: the 50 by 16 wordmark, glow colours `h` `#8c8c8c` and `H` `#3d3d3d`, and the docstring key line ("inner white glow, outer white glow").
- `tests/test_brand.py`: wordmark limits raised to 56 by 16, an exact 16-row check, a separator check, and the symmetry tests.
- `tests/ui/test_logo.py`: widths 61 to 68 and 65 to 72, indent widths 59 to 66 and 63 to 70, plain rows 7 to 8, glow SGR codes.
- `tests/golden/logo_dark_truecolor.txt` and `tests/golden/logo_light_truecolor.txt`: regenerated once each.

`sushicore/ui/logo.py` needed no change. Nothing was committed. Task 15's files were not touched.

Golden update: the owner approved this look, so replacing both goldens is an approved update. The final goldens were made with the strong white glow, `h` `#8c8c8c` (SGR `38;2;140;140;140`) and `H` `#3d3d3d` (SGR `38;2;61;61;61`). The light golden has no glow colour, so the colour change only altered the dark one. An earlier pass with the soft glow (`#6b6b6b`, `#2e2e2e`) was overwritten before this report; no golden from it remains.

The wordmark was compared with the plan's grid by a script that reads the plan file: `wordmark identical to plan: True 16`.

## Symmetry test

`tests/test_brand.py` cuts each wordmark line into letters by position (SUSHI: S U S H I, widths 6 6 6 6 2; SYSTEMS: S Y S T E M S, widths 6 6 6 6 6 8 6; one blank column between letters; letter rows 0-6 and 9-15). It checks that `U H I T Y M` equal their left-right mirror, that all five `S` equal their half turn, that every separator column is blank, and that rows 7 and 8 are blank. All pass.

## Failing run (tests first, old brand.py)

Command: `PYTHONPATH=D:/Projects/sushicore python -m pytest tests/test_brand.py tests/ui/test_logo.py tests/test_ui_architecture.py -q`, first with the soft glow codes, output filtered to the summary lines.

```
E       AssertionError: assert 14 == 16
E               AssertionError: assert {'.', 'w'} == {'.'}
E       assert 65 == 72
E        +  where 65 = Logo(indent=2, wordmark=True, glow=True).width
E       assert 61 == 68
E        +  where 61 = Logo(indent=2, wordmark=True, glow=False).width
E       assert 59 == 66
E        +  where 59 = Logo(indent=0, wordmark=True, glow=False).width
E       AssertionError: assert '\\x1b[38;2;107;107;107m\u2580' in '\\x1b[38;2;92;63;0m\u2580\\x1b[0m\\x1b[38;2;42;29;0m\u2584\\x1b[0m\\n'
FAILED tests/test_brand.py::test_the_wordmark_has_sixteen_rows - AssertionErr...
FAILED tests/test_brand.py::test_one_blank_column_separates_the_letters_and_two_blank_rows_the_lines
FAILED tests/test_brand.py::test_these_letters_read_the_same_mirrored_left_to_right[U]
FAILED tests/test_brand.py::test_these_letters_read_the_same_mirrored_left_to_right[H]
FAILED tests/test_brand.py::test_these_letters_read_the_same_mirrored_left_to_right[T]
FAILED tests/test_brand.py::test_these_letters_read_the_same_mirrored_left_to_right[Y]
FAILED tests/test_brand.py::test_these_letters_read_the_same_mirrored_left_to_right[M]
FAILED tests/test_brand.py::test_the_s_reads_the_same_after_a_half_turn
FAILED tests/ui/test_logo.py::test_the_glowing_lockup_is_eight_rows_and_seventy_two_columns
FAILED tests/ui/test_logo.py::test_the_plain_lockup_is_eight_rows_and_sixty_eight_columns
FAILED tests/ui/test_logo.py::test_width_counts_the_indent
FAILED tests/ui/test_logo.py::test_the_glow_rings_draw_in_their_own_colours_when_asked
12 failed, 81 passed in 0.36s
```

The failures are the old 14-row wordmark, old widths and the old amber glow codes, as the plan states. (The pytest output shows escape characters doubled inside its own assertion message; the test source holds a single `\x1b`.)

After changing `brand.py` to the soft colours, only the two goldens failed (`2 failed, 91 passed`). They were then regenerated.

## Changed decision: strong glow

The coordinator switched the colours to `#8c8c8c` and `#3d3d3d` mid-task. Test change first, `brand.py` still soft:

```
E       AssertionError: assert '\\x1b[38;2;140;140;140m\u2580' in '\\x1b[38;2;107;107;107m\u2580\\x1b[0m\\x1b[38;2;46;46;46m\u2584\\x1b[0m\\n'
FAILED tests/ui/test_logo.py::test_the_glow_rings_draw_in_their_own_colours_when_asked
1 failed, 92 passed in 0.25s
```

After `brand.py` changed to the strong colours, before the golden was regenerated:

```
FAILED tests/ui/test_logo.py::test_the_dark_logo_matches_its_golden_file - As...
1 failed, 92 passed in 0.25s
```

After `python regen_goldens.py` (throwaway script in the session scratchpad, UTF-8, `\n`), the dark golden holds `140;140;140` and `61;61;61` and no `107;107`:

```
wordmark identical to plan: True 16
```

## Passing runs

Acceptance run: `PYTHONPATH=D:/Projects/sushicore python -m pytest tests/test_brand.py tests/ui/test_logo.py tests/test_ui_architecture.py -v`, last line:

```
============================= 93 passed in 0.22s =============================
```

Full suite: `PYTHONPATH=D:/Projects/sushicore python -m pytest tests -q`:

```
........................................................................ [ 22%]
........................................................................ [ 44%]
........................................................................ [ 66%]
........................................................................ [ 88%]
.......................................                                  [100%]
327 passed in 0.90s
```

Nothing was ignored; Task 15's files were not failing at that moment.

## Syntax check

`python -m py_compile sushicore/brand.py tests/test_brand.py tests/ui/test_logo.py; echo "exit $?"`:

```
exit 0
```

## Measured sizes

`width` is the default indent 2; `indent=0` is the same logo without the indent.

```
glow=False wordmark=False width=16 indent0_width=14 rows=6
glow=False wordmark=True width=68 indent0_width=66 rows=8
glow=True wordmark=False width=20 indent0_width=18 rows=8
glow=True wordmark=True width=72 indent0_width=70 rows=8
```

## Plain-text rendering (`PYTHONIOENCODING=utf-8`, width 80)

`Logo(indent=0)`:

```
                ▄█▀▀▀▀ ██  ██ ▄█▀▀▀▀ ██  ██ ██
 ▄▄▀▀▀▀▀▀██▄    ▀█▄▄▄  ██  ██ ▀█▄▄▄  ██▄▄██ ██
▄██▀▀▀▀▀██▀██       ██ ██  ██     ██ ██  ██ ██
█████████▀████  ▀▀▀▀▀   ▀▀▀▀  ▀▀▀▀▀  ▀▀  ▀▀ ▀▀
██████████████   ▄▄▄▄▄ ▄▄  ▄▄  ▄▄▄▄▄ ▄▄▄▄▄▄ ▄▄▄▄▄▄ ▄▄    ▄▄  ▄▄▄▄▄
███▀▀██▀▀████▀  ██     ▀█▄▄█▀ ██       ██   ██     ███▄▄███ ██
 ▀▀▀▀▀▀▀▀▀▀▀     ▀▀▀█▄   ██    ▀▀▀█▄   ██   ██▀▀   ██ ██ ██  ▀▀▀█▄
                ▄▄▄▄█▀   ██   ▄▄▄▄█▀   ██   ██▄▄▄▄ ██    ██ ▄▄▄▄█▀
```

`Logo(indent=0, glow=True)` (plain text hides the glow colour, so the extra ring shows only as wider blocks):

```
   ▄▄▀▀▀▀▀▀▀▀▄      ▄█▀▀▀▀ ██  ██ ▄█▀▀▀▀ ██  ██ ██
 ▄▀▀▀▀▀▀▀▀▀██▀▀▄    ▀█▄▄▄  ██  ██ ▀█▄▄▄  ██▄▄██ ██
▄▀▀██▀▀▀▀▀██▀████       ██ ██  ██     ██ ██  ██ ██
███████████▀██████  ▀▀▀▀▀   ▀▀▀▀  ▀▀▀▀▀  ▀▀  ▀▀ ▀▀
██████████████████   ▄▄▄▄▄ ▄▄  ▄▄  ▄▄▄▄▄ ▄▄▄▄▄▄ ▄▄▄▄▄▄ ▄▄    ▄▄  ▄▄▄▄▄
█████▀▀██▀▀████▀▀▀  ██     ▀█▄▄█▀ ██       ██   ██     ███▄▄███ ██
 ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀     ▀▀▀█▄   ██    ▀▀▀█▄   ██   ██▀▀   ██ ██ ██  ▀▀▀█▄
   ▀▀▀▀▀▀▀▀▀▀▀      ▄▄▄▄█▀   ██   ▄▄▄▄█▀   ██   ██▄▄▄▄ ██    ██ ▄▄▄▄█▀
```

## What was not done

- No commit, no edit of `logo.py`, `pyproject.toml`, any `__init__.py`, the docs, the plan, or the changelog.
- No visual check in a real dark terminal; the strong glow was verified only through the SGR codes in the golden and the tiny-grid test.
