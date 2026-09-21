# Task 7 — `HelpModel` and the Click reader

Worker report for `docs/agent/plans/2026-09-21-terminal-components.md`, Task 7.

## Files written

| File | State |
| --- | --- |
| `sushicore/help/__init__.py` | Created; the plan's docstring only, no re-exports |
| `sushicore/help/model.py` | Created; `HelpSection` and `HelpModel` |
| `sushicore/help/from_click.py` | Created; `build_model` and its private readers |
| `tests/help/__init__.py` | Created, empty |
| `tests/help/test_from_click.py` | Created; the plan's 11 tests plus one Typer test |
| `docs/agent/reports/2026-09-21-terminal-components-task-7.md` | This report |

Nothing else was touched. `pyproject.toml`, `README.md`, `docs/README.md` and
`docs/reference/CHANGELOG.md` are unchanged, and so is everything under `sushicore/ui/`,
`tests/ui/` and `tests/golden/`.

`HelpSection(heading, entries)`, `HelpModel(name, description, usage, is_root, commands,
arguments, options, examples)` and `build_model(command, ctx)` carry the names and fields the
plan gives, so Tasks 9 and 10 can be written against them.

## Step 2: the failing run

```
$ python -m pytest tests/help/test_from_click.py -v
rootdir: D:\Projects\sushicore
configfile: pyproject.toml
plugins: anyio-4.12.1
collecting ... collected 0 items / 1 error

=================================== ERRORS ====================================
_______________ ERROR collecting tests/help/test_from_click.py ________________
ImportError while importing test module 'D:\Projects\sushicore\tests\help\test_from_click.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
C:\ProgramData\Miniconda\Lib\importlib\__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\help\test_from_click.py:6: in <module>
    from sushicore.help.from_click import build_model
E   ModuleNotFoundError: No module named 'sushicore.help'
=========================== short test summary info ===========================
ERROR tests/help/test_from_click.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
============================== 1 error in 0.14s ===============================
```

## Step 4: the passing run

```
$ python -m pytest tests/help/test_from_click.py -v
platform win32 -- Python 3.13.13, pytest-9.1.1, pluggy-1.6.0
rootdir: D:\Projects\sushicore
configfile: pyproject.toml
plugins: anyio-4.12.1
collecting ... collected 12 items

tests/help/test_from_click.py::test_commands_are_grouped_by_panel_in_order_of_first_appearance PASSED [  8%]
tests/help/test_from_click.py::test_a_command_with_no_panel_falls_into_commands PASSED [ 16%]
tests/help/test_from_click.py::test_a_placeholder_panel_is_not_a_heading PASSED [ 25%]
tests/help/test_from_click.py::test_hidden_commands_are_left_out PASSED  [ 33%]
tests/help/test_from_click.py::test_options_come_from_the_help_records PASSED [ 41%]
tests/help/test_from_click.py::test_an_argument_without_a_record_falls_back_to_its_metavar PASSED [ 50%]
tests/help/test_from_click.py::test_usage_and_name_use_the_command_path PASSED [ 58%]
tests/help/test_from_click.py::test_only_the_top_command_is_the_root PASSED [ 66%]
tests/help/test_from_click.py::test_a_leaf_has_no_command_sections PASSED [ 75%]
tests/help/test_from_click.py::test_examples_split_the_command_from_its_note_and_skip_blank_lines PASSED [ 83%]
tests/help/test_from_click.py::test_the_description_joins_wrapped_lines_and_stops_at_a_form_feed PASSED [ 91%]
tests/help/test_from_click.py::test_a_typer_app_groups_by_its_panels_and_keeps_typer_help_records PASSED [100%]

============================= 12 passed in 0.14s ==============================
```

One line of the plan's test text ran to 104 columns; it became two lines, and the test was
re-run after the edit:

```
$ python -m pytest tests/help/test_from_click.py -q
............                                                             [100%]
12 passed in 0.14s
```

## Syntax check

```
$ python -m py_compile sushicore/help/__init__.py sushicore/help/model.py \
    sushicore/help/from_click.py tests/help/__init__.py tests/help/test_from_click.py
py_compile: no output, exit 0
```

## The whole suite

```
$ python -m pytest tests -q
........................................................................ [ 38%]
........................................................................ [ 76%]
.............................................                            [100%]
189 passed in 0.50s
```

No failure belonging to Tasks 4, 5 or 6 appeared.

## The Typer test

`test_a_typer_app_groups_by_its_panels_and_keeps_typer_help_records` builds a two-command
`typer.Typer`, converts it with `typer.main.get_command(app)`, and checks `build_model` on the
real objects: `grow` names the panel `Garden`, `rest` names none and lands under `Commands`, and
the leaf's entries are Typer's own records, `("MODULE", "The module.  \\[required]")` and
`("--kind TEXT", "Kind [x].  \\[default: a]")`. Typer escapes the markup itself, so the reader
passes both strings through untouched.

## Three things in the plan's code that were changed

**The placeholder guard was too narrow.** The plan tests `isinstance(panel, str)` for
`rich_help_panel` but reads `command.help` and `command.epilog` with `or ""`. Typer 0.20 hands a
`DefaultPlaceholder` to `rich_help_panel`, and that object is truthy, so the same `or ""` on
`help` or `epilog` would have let a placeholder through to `.split("\f")` and raised
`AttributeError`. One private `_text(value)` now answers the question once for all four reads:
a string stays, anything else becomes empty. Measured here, a Typer command with no `help` or
`epilog` carries `None` in both, so nothing in the suite depended on this; the guard covers the
case where a future Typer version stops normalising them.

**`make_metavar` has two signatures.** Click 8.2.1 requires the context, Click 8.1 takes none,
and the module may not import Click to find out which it is talking to. `_metavar` reads
`inspect.signature` and calls whichever the object accepts, rather than catching a `TypeError`
that could have come from inside the call.

**`param.help` could be a placeholder too.** The metavar fallback now goes through `_text` for
the same reason as the description.

## Not done

- No commit, no changelog line, no re-exports in `sushicore/help/__init__.py`; those belong to
  the orchestrator.
- `sushicore/help/page.py` is Task 9 and was not written.
- The reader was exercised against Click 8.2.1 and Typer 0.20 only, the versions installed here.
  Older Click is handled by the `make_metavar` branch but no environment was built to run it.
