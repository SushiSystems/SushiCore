# Task 4 report: Logo

## Files changed

- `sushicore/ui/logo.py` (new): `Logo(indent: int = 2)`, `@final`, `@dataclass(frozen=True, slots=True)`, `render(theme) -> Text`, plus the private `_cell` helper.
- `tests/ui/test_logo.py` (new): the five tests from the plan, unchanged.
- `tests/golden/logo_truecolor.txt` (new): truecolour output of `Logo()` at width 80, UTF-8, `\n` newlines, no `\r`. 10 rows.

The implementation follows the plan's code. One deviation: `render` is annotated `-> Text`, as the task's interface line says, instead of `RenderableType`, so the unused `RenderableType` import is gone. `Text` is a `RenderableType`, so `Component` still holds.

## Commands run

Step 2, before `logo.py` existed:

```
$ python -m pytest tests/ui/test_logo.py -v
collecting ... collected 0 items / 1 error
tests\ui\test_logo.py:6: in <module>
    from sushicore.ui.logo import Logo
E   ModuleNotFoundError: No module named 'sushicore.ui.logo'
============================== 1 error in 0.15s ===============================
```

Golden, made once by the scratchpad script `make_logo_golden.py` (`capture_ansi(Logo(), width=80)` written with `encoding="utf-8", newline="\n"`):

```
$ PYTHONPATH=. python $SCRATCH/make_logo_golden.py && wc -l tests/golden/logo_truecolor.txt
10 tests/golden/logo_truecolor.txt
$ grep -c $'\r' tests/golden/logo_truecolor.txt
0
```

Step 4:

```
$ python -m pytest tests/ui/test_logo.py tests/test_ui_architecture.py -v
collected 26 items
tests/ui/test_logo.py::test_two_pixel_rows_become_one_terminal_row PASSED
tests/ui/test_logo.py::test_indent_prefixes_every_non_empty_row PASSED
tests/ui/test_logo.py::test_each_cell_picks_the_block_that_shows_its_two_pixels PASSED
tests/ui/test_logo.py::test_two_different_colours_share_one_cell_as_foreground_and_background PASSED
tests/ui/test_logo.py::test_the_logo_matches_its_golden_file PASSED
tests/test_ui_architecture.py::test_file_defines_one_public_class_named_after_the_file[logo.py] PASSED
tests/test_ui_architecture.py::test_component_is_a_frozen_dataclass_with_render[logo.py] PASSED
tests/test_ui_architecture.py::test_component_uses_slots[logo.py] PASSED
tests/test_ui_architecture.py::test_component_is_marked_final[logo.py] PASSED
tests/test_ui_architecture.py::test_file_imports_only_what_a_component_may[logo.py] PASSED
(plus the protocol case and the header.py, panel.py, table.py cases, all PASSED)
============================= 26 passed in 0.14s ==============================
```

Syntax check (line 5, Python variant):

```
$ python -m py_compile sushicore/ui/logo.py tests/ui/test_logo.py && echo compiled-ok
compiled-ok
```

Full suite:

```
$ python -m pytest tests -q
167 passed in 0.54s
```

The suite already contained the other workers' `header.py`, `panel.py` and `table.py`; their architecture cases pass too.

## Plain-text rendering of `Logo(indent=0)`

Ten rows, from the current `K_LOGO_PIXELS` (20 pixel rows, 22 columns):

```
   ▄▄▄▀▀▀▀▀▀▀████▄▄
 ▄▀████████████▀███▄
▄▀████▀▀██▀▀████▀████
████▀████████▀███▀███▄
██████████████████████
███▀██████████████████
████▀███▀▀▀▀▀▀▀███████
▀▀███▀▀▀█████▀███████▀
 ▀▀█████████████▀██▀
   ▀▀▀▀▀▀▀▀▀▀▀▀▀▀
```

## What was not done

- I did not read the golden back with the Read tool; I checked it with `wc -l` (10 rows), `od -c` (starts with the `\x1b[38;2;26;28;32m` escape for nori) and `grep -c` for `\r` (0). The row count matches the ten rows above.
- No commit, and no edits to `pyproject.toml`, `README.md`, `docs/README.md`, the changelog or `sushicore/ui/__init__.py`.
- No `sushicore/ui/__init__.py` re-export of `Logo`; that is the orchestrator's.
- Running the print script under the default Windows code page raised `UnicodeEncodeError` (cp1252 stdout); I reran it with `PYTHONIOENCODING=utf-8`. This does not affect the tests, which compare strings in memory.
- An odd number of pixel rows would drop the last row (`zip` of the even and odd slices). The current grid has 20 rows, and no test covers the odd case.
