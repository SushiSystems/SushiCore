# Task 14 — background detection

Plan: `docs/agent/plans/2026-09-21-terminal-components.md`, Wave 6a.

## Files changed

- Created `sushicore/terminal_background.py`: `K_DARK`, `K_LIGHT`, `K_AUTO`, `K_VALUES`,
  `K_VARIABLE`, `K_DARK_INDICES`, `is_dark_background(setting, environ)` and the private
  `_names_a_dark_colour`.
- `sushicore/config.py`: `AppearanceSpec.background: str = "auto"`; `load_appearance` reads
  `[cli] background` (also under `[cli.<platform>]`, through the existing `_merge_cli_table`)
  and `SUSHI_CLI_BACKGROUND`, and falls back to `"auto"` for a value outside `K_VALUES`. The
  schema in the module docstring gained the line.
- `sushicore/console.py`: `Console.__init__` takes `dark_background: bool = False` and stores
  it; a read-only `dark_background` property returns it.
- `sushicore/__init__.py`: `build_console` passes
  `is_dark_background(spec.background, os.environ)` to the console.
- Created `tests/test_terminal_background.py` (13 cases) and
  `tests/test_appearance_background.py` (10 cases).

## Verification

Baseline before any edit:

```
$ python -m pytest tests -q
........................................................................ [ 31%]
........................................................................ [ 62%]
........................................................................ [ 93%]
................                                                         [100%]
232 passed in 0.62s
```

The new tests, written first, failing:

```
$ python -m pytest tests/test_terminal_background.py tests/test_appearance_background.py -v
collecting ... collected 10 items / 1 error

=================================== ERRORS ====================================
_____________ ERROR collecting tests/test_terminal_background.py ______________
ImportError while importing test module 'D:\Projects\sushicore\tests\test_terminal_background.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
C:\ProgramData\Miniconda\Lib\importlib\__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\test_terminal_background.py:5: in <module>
    from sushicore.terminal_background import is_dark_background
E   ModuleNotFoundError: No module named 'sushicore.terminal_background'
=========================== short test summary info ===========================
ERROR tests/test_terminal_background.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
============================== 1 error in 0.16s ===============================
```

Collection stops at the missing module, so the appearance file ran on its own:

```
$ python -m pytest tests/test_appearance_background.py -v
=========================== short test summary info ===========================
FAILED tests/test_appearance_background.py::test_background_defaults_to_auto
FAILED tests/test_appearance_background.py::test_the_cli_table_sets_the_background
FAILED tests/test_appearance_background.py::test_the_platform_table_overrides_the_common_one
FAILED tests/test_appearance_background.py::test_the_environment_overrides_the_file
FAILED tests/test_appearance_background.py::test_an_unknown_background_falls_back_to_auto
FAILED tests/test_appearance_background.py::test_a_console_reports_the_background_it_was_built_with
FAILED tests/test_appearance_background.py::test_a_console_assumes_a_light_background_by_default
FAILED tests/test_appearance_background.py::test_build_console_takes_the_background_from_the_config
FAILED tests/test_appearance_background.py::test_build_console_falls_back_to_colorfgbg
FAILED tests/test_appearance_background.py::test_build_console_without_a_setting_or_colorfgbg_is_not_dark
============================= 10 failed in 0.29s ==============================
```

After the change:

```
$ python -m pytest tests/test_terminal_background.py tests/test_appearance_background.py -v
tests/test_terminal_background.py::test_dark_wins_over_a_light_colorfgbg PASSED [  4%]
tests/test_terminal_background.py::test_light_wins_over_a_dark_colorfgbg PASSED [  8%]
tests/test_terminal_background.py::test_auto_reads_a_dark_background_index[15;0] PASSED [ 13%]
tests/test_terminal_background.py::test_auto_reads_a_dark_background_index[15;default;0] PASSED [ 17%]
tests/test_terminal_background.py::test_auto_reads_a_dark_background_index[7;6] PASSED [ 21%]
tests/test_terminal_background.py::test_auto_reads_a_dark_background_index[7;8] PASSED [ 26%]
tests/test_terminal_background.py::test_auto_reads_anything_else_as_not_dark[0;15] PASSED [ 30%]
tests/test_terminal_background.py::test_auto_reads_anything_else_as_not_dark[0;7] PASSED [ 34%]
tests/test_terminal_background.py::test_auto_reads_anything_else_as_not_dark[15;9] PASSED [ 39%]
tests/test_terminal_background.py::test_auto_reads_anything_else_as_not_dark[] PASSED [ 43%]
tests/test_terminal_background.py::test_auto_reads_anything_else_as_not_dark[garbage] PASSED [ 47%]
tests/test_terminal_background.py::test_auto_reads_anything_else_as_not_dark[15;-1] PASSED [ 52%]
tests/test_terminal_background.py::test_auto_without_the_variable_is_not_dark PASSED [ 56%]
tests/test_appearance_background.py::test_background_defaults_to_auto PASSED [ 60%]
tests/test_appearance_background.py::test_the_cli_table_sets_the_background PASSED [ 65%]
tests/test_appearance_background.py::test_the_platform_table_overrides_the_common_one PASSED [ 69%]
tests/test_appearance_background.py::test_the_environment_overrides_the_file PASSED [ 73%]
tests/test_appearance_background.py::test_an_unknown_background_falls_back_to_auto PASSED [ 78%]
tests/test_appearance_background.py::test_a_console_reports_the_background_it_was_built_with PASSED [ 82%]
tests/test_appearance_background.py::test_a_console_assumes_a_light_background_by_default PASSED [ 86%]
tests/test_appearance_background.py::test_build_console_takes_the_background_from_the_config PASSED [ 91%]
tests/test_appearance_background.py::test_build_console_falls_back_to_colorfgbg PASSED [ 95%]
tests/test_appearance_background.py::test_build_console_without_a_setting_or_colorfgbg_is_not_dark PASSED [100%]

============================= 23 passed in 0.18s ==============================
```

Syntax check:

```
$ python -m py_compile sushicore/terminal_background.py sushicore/config.py sushicore/console.py sushicore/__init__.py tests/test_terminal_background.py tests/test_appearance_background.py; echo "exit $?"
exit 0
```

## The full suite

`python -m pytest tests -q` does not collect right now, and every error comes from the two
files other workers hold:

```
$ python -m pytest tests -q
=========================== short test summary info ===========================
ERROR tests/test_brand.py
ERROR tests/ui/test_definition_list.py
ERROR tests/ui/test_logo.py
!!!!!!!!!!!!!!!!!!! Interrupted: 3 errors during collection !!!!!!!!!!!!!!!!!!!
3 errors in 0.31s
```

The errors are `ImportError: cannot import name 'K_FOREGROUND_KEY' from 'sushicore.brand'`
(Task 13, mid-write), `ImportError: cannot import name 'capture' from 'tests.ui.capture'` and
`SyntaxError: unterminated string literal` in `tests/ui/test_definition_list.py` line 32
(Task 16, mid-write). They were left alone. Everything outside those directories passes:

```
$ python -m pytest tests -q --ignore=tests/ui --ignore=tests/help --ignore=tests/test_brand.py
........................................................................ [ 36%]
........................................................................ [ 72%]
........................................................                 [100%]
200 passed in 0.59s
```

The acceptance criterion's second half, `python -m pytest tests -q` green in full, is therefore
unproven. The orchestrator should re-run it once Waves 13 and 16 land.

## Decisions where the plan left room

- The plan names `K_DARK`, `K_LIGHT`, `K_AUTO` and `K_VALUES`. Two more constants were needed:
  `K_VARIABLE = "COLORFGBG"` and `K_DARK_INDICES`, the frozen set `{0..6, 8}`.
- "A non-negative integer" is read with `str.isdecimal()`, so `"-1"` and `""` are unknown, and
  so is a superscript digit that `str.isdigit()` would accept and `int()` would reject. A case
  for `"15;-1"` is in the tests.
- `config.py` imports `K_AUTO` and `K_VALUES` from `terminal_background`, which keeps the list
  of valid values in one place. `terminal_background` imports nothing from the package, so the
  dependency points down.
- `is_dark_background` is not added to `sushicore.__all__`; the dispatch said to wire
  `build_console` only, and the plan names the function by its module path.

## Not done

- No commit, and no edit to `pyproject.toml`, `README.md`, `docs/README.md`,
  `docs/reference/CHANGELOG.md`, the specs, the plans, `sushicore/ui/__init__.py` or
  `sushicore/help/__init__.py`.
- Nothing in Tasks 13, 15 or 16: `Logo`, `brand.py`, `choose_logo` and the help page still
  ignore `Console.dark_background`. Task 15 connects them.
