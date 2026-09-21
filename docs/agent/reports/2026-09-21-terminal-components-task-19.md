# Task 19 — a grouped and coloured `Table`

Wave 7a of `docs/agent/plans/2026-09-21-terminal-components.md`. Written 2026-09-21.

## Files changed

- `sushicore/ui/table.py` — `group_by` field, `K_STATUS_STYLES`, the grouped layout.
- `sushicore/renderer.py` — `group_by: str | None = None` on the `Renderer` Protocol and on all
  three renderers; only `RichRenderer` acts on it.
- `sushicore/console.py` — `Console.table(..., *, group_by=None)`, forwarded only when set.
- `tests/ui/test_table.py` — 14 tests added, the 3 existing ones untouched.
- `tests/test_renderer_components.py` — one grouped table through `RichRenderer`.
- `tests/test_console_semantics.py` — three tests: the keyword left out, the keyword forwarded,
  and an old-style renderer serving an ungrouped call.
- `tests/test_json_renderer.py` — the `table` event compared byte for byte with and without
  `group_by`.

## Decisions the plan left open

- The column headers are indented two spaces, like the rows, because the plan asks them to line
  up with the columns below them. The mock drew them flush left.
- The rule under the headers is a `rich.rule.Rule` in `theme.muted`, so it spans the whole
  console width. The last column already claims the rest of that width, so a shorter rule would
  end in the middle of the `Detail` column.
- `group_by` is checked in `__post_init__`, so a wrong column name fails where it is written
  rather than where the table is drawn.
- The status map is matched on the cell's whole text, upper-cased, with no stripping.

## The grouped table at width 100

Built from the fixed rows in `tests/ui/test_table.py`, through `capture(_inventory(), width=100)`:

```
Environment inventory

  Component    Status      Detail
────────────────────────────────────────────────────────────────────────────────────────────────────
shared
  python       OK          C:\Users\sushi\AppData\Local\Programs\Python\python.EXE
  build_tools  NOT NEEDED  C++ compiler and core build tools (gcc, g++, make). Any GCC >= 9 suffices
                           for the intel-llvm -fsycl host pass. (nothing to install on windows)
  GPU vendor   OK          NVIDIA - installs CUDA toolkit

sushiruntime
  adaptivecpp  MISSING     AdaptiveCpp (acpp)
```

## The status codes

From `capture_ansi(_inventory(), width=100)` with the default `Theme`, the row lines that carry a
status, first 80 characters, as Python reprs:

```
'  python       \x1b[1;32mOK        \x1b[0m  C:\\Users\\sushi\\AppData\\Local\\Programs\\Pyth'
'  build_tools  \x1b[2mNOT NEEDED\x1b[0m  C++ compiler and core build tools (gcc, g++, '
'  GPU vendor   \x1b[1;32mOK        \x1b[0m  NVIDIA - installs CUDA toolkit            '
'  adaptivecpp  \x1b[1;31mMISSING   \x1b[0m  AdaptiveCpp (acpp)                        '
```

`OK` carries `\x1b[1;32m` (`success`, `bold green`), `MISSING` carries `\x1b[1;31m` (`error`,
`bold red`), `NOT NEEDED` carries `\x1b[2m` (`muted`, `dim`). The style covers the cell's padding
as well as its word, which costs nothing with a foreground-only style.

## Commands

The tests first, against the old `Table`:

```
$ python -m pytest tests/ui/test_table.py -q
FAILED tests/ui/test_table.py::test_group_by_must_name_one_of_the_columns - T...
FAILED tests/ui/test_table.py::test_the_grouped_table_keeps_its_title_and_a_blank_line_under_it
FAILED tests/ui/test_table.py::test_the_column_headers_are_drawn_once_without_the_group_column
FAILED tests/ui/test_table.py::test_a_muted_rule_separates_the_headers_from_the_first_group
FAILED tests/ui/test_table.py::test_each_group_value_becomes_a_heading_in_order_of_first_appearance
FAILED tests/ui/test_table.py::test_one_blank_line_separates_the_groups_and_none_follows_the_last
FAILED tests/ui/test_table.py::test_the_group_column_is_gone_from_the_rows - ...
FAILED tests/ui/test_table.py::test_every_column_but_the_last_lines_up_across_the_groups
FAILED tests/ui/test_table.py::test_only_the_last_column_wraps - TypeError: T...
FAILED tests/ui/test_table.py::test_a_wrapped_detail_keeps_its_first_word_under_the_first_line
FAILED tests/ui/test_table.py::test_an_empty_group_value_is_drawn_as_a_dash
FAILED tests/ui/test_table.py::test_a_status_cell_takes_the_theme_style_its_word_maps_to
FAILED tests/ui/test_table.py::test_a_status_word_is_recognised_whatever_its_case
13 failed, 4 passed in 0.15s
```

Every one of the thirteen failed on `TypeError: Table.__init__() got an unexpected keyword
argument 'group_by'`. The three renderer-side tests failed the same way:

```
$ python -m pytest tests/test_json_renderer.py tests/test_console_semantics.py tests/test_renderer_components.py -q
E       TypeError: RichRenderer.table() got an unexpected keyword argument 'group_by'
FAILED tests/test_json_renderer.py::test_the_table_event_is_byte_identical_with_and_without_a_grouping_column
FAILED tests/test_console_semantics.py::test_console_forwards_the_grouping_column_when_it_is_given
FAILED tests/test_renderer_components.py::test_grouped_table_prints_a_heading_per_group_without_the_group_column
3 failed, 28 passed in 0.21s
```

After the implementation, the whole suite in the default order:

```
$ python -m pytest tests -q
........................................................................ [ 41%]
........................................................................ [ 62%]
........................................................................ [ 82%]
...........................................................              [100%]
347 passed in 0.83s
```

and with the top-level test files reversed:

```
$ python -m pytest $(ls tests/test_*.py | sort -r) tests/ui tests/help -q
........................................................................ [ 41%]
........................................................................ [ 62%]
........................................................................ [ 82%]
...........................................................              [100%]
347 passed in 0.91s
```

The baseline was 328; the 19 new tests bring it to 347 either way.

The syntax check:

```
$ python -m py_compile sushicore/ui/table.py sushicore/renderer.py sushicore/console.py tests/ui/test_table.py tests/test_renderer_components.py tests/test_console_semantics.py tests/test_json_renderer.py; echo "exit $?"
exit 0
```

Every command ran from `D:/Projects/sushicore` with `PYTHONPATH=D:/Projects/sushicore`.

## Not done

- No commit, and no edit to `pyproject.toml`, `README.md`, `docs/README.md`,
  `docs/reference/CHANGELOG.md`, the specs, the plans or any `__init__.py`.
- Task 20 (`hub doctor` in `D:/Projects/sushistack`) is untouched.
- One line in `tests/test_json_renderer.py` is 111 characters long. It predates this task and I
  left it alone.
