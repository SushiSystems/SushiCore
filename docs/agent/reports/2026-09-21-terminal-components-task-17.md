# Task 17: trim the logo's empty margin

Date: 2026-09-21

## Files changed

- `sushicore/ui/logo.py`: new `_trimmed(grid, colours)`; `_pixels` takes the trimmed mark; `width` and `render` both call `_trimmed(K_MARK_PIXELS, _colours(self.glow))`, so they cannot disagree. The module globals are still read at call time.
- `tests/ui/test_logo.py`: size tests split into glow and plain, plus the trimming tests.
- `tests/golden/logo_light_truecolor.txt`: replaced. This is the owner-approved update Task 17 names (the owner asked for a light terminal that stays normal). The dark golden is untouched.

## Rule as built

`_trimmed` pads the grid to one width, finds the pixel keys that have a colour in the chosen palette, cuts leading and trailing rows and columns without one, and appends one transparent row at the bottom when the row count is odd. A grid with no coloured pixel is returned as it is. The wordmark grid is not trimmed. `_cell`, the `Logo` fields, `@final`, the frozen slots dataclass and the import list are unchanged.

## Verification

Failing run, tests written first, before `logo.py` changed:

```
FAILED tests/ui/test_logo.py::test_the_plain_lockup_is_seven_rows_and_sixty_one_columns
FAILED tests/ui/test_logo.py::test_the_plain_mark_alone_is_six_rows_and_sixteen_columns
FAILED tests/ui/test_logo.py::test_width_counts_the_indent - assert 63 == 59
FAILED tests/ui/test_logo.py::test_the_widest_row_is_as_wide_as_the_width_says[False-False]
FAILED tests/ui/test_logo.py::test_the_plain_logo_has_no_blank_edge_row_or_column[False]
FAILED tests/ui/test_logo.py::test_the_plain_logo_has_no_blank_edge_row_or_column[True]
FAILED tests/ui/test_logo.py::test_the_plain_mark_alone_has_no_blank_first_line
FAILED tests/ui/test_logo.py::test_transparent_edge_rows_and_columns_are_dropped_without_the_glow
FAILED tests/ui/test_logo.py::test_an_odd_trimmed_row_count_gains_one_transparent_row_at_the_bottom
FAILED tests/ui/test_logo.py::test_the_trimmed_mark_sets_the_width_beside_the_wordmark
10 failed, 18 passed in 0.16s
```

The failures are the stated reason: the plain logo was 65 columns and 8 rows, the mark alone 20 columns, and a blank first row and two blank columns were drawn. The 18 that passed are the glow-on tests and the untouched ones, which is the "glow unchanged" half of the criterion.

Passing runs:

```
$ python -m py_compile sushicore/ui/logo.py tests/ui/test_logo.py; echo "exit $?"
exit 0

$ PYTHONPATH=D:/Projects/sushicore python -m pytest tests/ui/test_logo.py -q
............................                                             [100%]
28 passed in 0.13s

$ PYTHONPATH=D:/Projects/sushicore python -m pytest tests -q
........................................................................ [ 48%]
........................................................................ [ 72%]
........................................................................ [ 97%]
........                                                                 [100%]
296 passed in 0.82s
```

Dark golden checksum, before my changes and after (identical):

```
34e1e14c275fa99e9288bcc87f7c225ad7f421047c871d8befd4356264332bdb *tests/golden/logo_dark_truecolor.txt
34e1e14c275fa99e9288bcc87f7c225ad7f421047c871d8befd4356264332bdb *tests/golden/logo_dark_truecolor.txt
```

The light golden went from `3e882cfb...6b5b` to `7b7849e4876aea67c552d28a0145a036e0dcd1bc157eff5af498aa8f307683ef`. I generated it from `capture_ansi(Logo(), width=80)` after the tests passed against the new code.

Plain-text rendering under `PYTHONIOENCODING=utf-8` (`capture_raw`, width 80):

```
Logo(indent=0)
   ▄▄▄▄▄▄▄▄     ▄█▀▀▀ ██ ██ ▄█▀▀▀ ██ ██ ██                 
 ▀███████▀██▄    ▀▀█▄ ██ ██  ▀▀█▄ █████ ██                 
██▀█████▀████▄  ▄▄▄█▀ ▀█▄█▀ ▄▄▄█▀ ██ ██ ██                 
██████████████                                             
██▀█▀▀▀▀▀▀████  ▄█▀▀▀ ██ ██ ▄█▀▀▀ ▀▀█▀▀ ██▀▀▀ ███▄███ ▄█▀▀▀
▀▀███▀▀███▀█▀    ▀▀█▄  ▀█▀   ▀▀█▄   █   ██▀▀  ██▀█▀██  ▀▀█▄
   ▀▀▀▀▀▀▀      ▄▄▄█▀   █   ▄▄▄█▀   █   ██▄▄▄ ██   ██ ▄▄▄█▀

Logo(indent=0, glow=True)
   ▄▄▀▀▀▀▀▀▀▀▄       ▄▄▄▄ ▄▄ ▄▄  ▄▄▄▄ ▄▄ ▄▄ ▄▄                 
 ▄▀▀▀▀▀▀▀▀▀██▀▀▄    ▀█▄▄  ██ ██ ▀█▄▄  ██▄██ ██                 
▄▀▀██▀▀▀▀▀██▀████      ██ ██ ██    ██ ██▀██ ██                 
███████████▀██████  ▀▀▀▀   ▀▀▀  ▀▀▀▀  ▀▀ ▀▀ ▀▀                 
██████████████████   ▄▄▄▄ ▄▄ ▄▄  ▄▄▄▄ ▄▄▄▄▄ ▄▄▄▄▄ ▄▄▄ ▄▄▄  ▄▄▄▄
█████▀▀██▀▀████▀▀▀  ▀█▄▄  ▀█▄█▀ ▀█▄▄    █   ██▄▄  ███████ ▀█▄▄ 
 ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀       ██   █      ██   █   ██    ██ ▀ ██    ██
   ▀▀▀▀▀▀▀▀▀▀▀      ▀▀▀▀    ▀   ▀▀▀▀    ▀   ▀▀▀▀▀ ▀▀   ▀▀ ▀▀▀▀ 

Logo(indent=0, wordmark=False)
 ▄▄▀▀▀▀▀▀██▄  
▄██▀▀▀▀▀██▀██ 
█████████▀████
██████████████
███▀▀██▀▀████▀
 ▀▀▀▀▀▀▀▀▀▀▀  
```

The glow rendering is plain text, so colour differences show only as block shapes; the byte-for-byte check of the glow is the dark golden.

## Not done

- No commit, and no edit to `pyproject.toml`, `README.md`, `docs/README.md`, the changelog, specs, plans or any `__init__.py`.
- Task 15's files were not touched.
- `python -m pytest tests -q` is 296 passed with Task 15's worker possibly writing at the same time; I ran it once, at the time shown above.
