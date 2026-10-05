# Task 21: a bracket in table data stays text

Date: 2026-09-21. Repository: `D:/Projects/sushicore`. Nothing committed.

## Files changed

- `sushicore/markup.py` (new): `escape_unknown_tags(text, known_styles)` plus three private helpers.
- `sushicore/ui/table.py`: `_cell` routes every non-status cell through the helper. The flat and the grouped layout both build their cells only through `_cell`, so this is the single place.
- `tests/test_markup.py` (new): 24 tests.
- `tests/ui/test_table.py`: 5 tests appended, existing ones untouched.
- `tests/test_ui_architecture.py`: `sushicore.markup` added to `K_ALLOWED_INTERNAL`, nothing else.

`sushicore/markup.py` is imported only by `ui/table.py`. `sushicore/__init__.py` was not touched.

## Reproduction before

Script: a flat and a grouped `Table` holding `Dear ImGui (imgui[glfw-binding,opengl3-binding])`, printed through `tests.ui.capture.capture`.

```
Name   Detail
─────────────────────────
a      Dear ImGui (imgui)

  Name  Detail
────────────────────────────────────────────────────────────────────────────────
o
  a     Dear ImGui (imgui)
```

## Tests written first, and failing for the stated reason

`tests/test_markup.py` failed at collection with `ModuleNotFoundError: No module named 'sushicore.markup'`. The new table tests, before the change:

```
FAILED tests/ui/test_table.py::test_a_bracket_that_names_no_style_stays_in_a_flat_cell
FAILED tests/ui/test_table.py::test_a_bracket_that_names_no_style_stays_in_a_grouped_cell
FAILED tests/ui/test_table.py::test_a_styled_cell_may_hold_a_bracket_that_names_no_style
3 failed, 19 passed in 0.11s
```

The failure text showed `Dear ImGui (imgui)` where the whole cell was expected. The two tests that check an `[error]FAIL[/error]` cell is styled passed before and after, as they should: they guard against a regression.

## Reproduction after

```
Name   Detail
───────────────────────────────────────────────────────
a      Dear ImGui (imgui[glfw-binding,opengl3-binding])

  Name  Detail
────────────────────────────────────────────────────────────────────────────────
o
  a     Dear ImGui (imgui[glfw-binding,opengl3-binding])
```

## Verification

```
$ python -m pytest tests -q
376 passed in 0.99s

$ python -m pytest $(ls tests/test_*.py | sort -r) tests/ui tests/help -q
376 passed in 1.04s

$ python -m py_compile sushicore/markup.py sushicore/ui/table.py tests/test_markup.py tests/ui/test_table.py tests/test_ui_architecture.py; echo "exit $?"
exit 0

$ python -c "import sys, sushicore; print('sushicore.markup' in sys.modules, 'rich' in sys.modules)"
False False
```

All commands ran with `PYTHONPATH=D:/Projects/sushicore`. `tests/test_renderer_components.py` is inside both runs and passes. No line is over 100 columns.

## Decisions on the edge cases

- **Which exception means "not a style".** `Style.parse` raises `rich.errors.StyleSyntaxError` for every failure, and it wraps colour errors itself. `rich.errors.ColorParseError`, which the plan names, does not exist (in Rich 15.0.0 it lives in `rich.color` and never escapes `Style.parse`). The helper catches `StyleSyntaxError` only.
- **`[0]`, `[1;2]`, `[ x ]`.** `Style.parse` raises for each, so they are escaped (`\[0]`). They print literally, with or without the escape.
- **`[]` and `[ ]`.** Both left alone: an empty name by the plan's rule, a blank one because `Style.parse(" ")` succeeds and returns the null style. Rich never reads either as a tag.
- **Backslashes.** Rich's own rule: a `[` after an odd number of backslashes is already escaped and stays as it is; after an even number (0, 2) it is not, and one backslash is inserted. `\\[x]` becomes `\\\[x]`, which Rich draws as `\[x]`, the same as the unescaped markup meant.
- **`[link https://example.com]x[/link]`.** The bracket is left untouched, but Rich itself raises `MarkupError` on that spelling, because the opening tag's name is the whole `link https://example.com`. The working forms are `[link=https://example.com]x[/link]` and `[link https://example.com]x[/]`. Both are tested and stay links (the span style is `link https://example.com`).
- **Closing tags.** `[/name]` is kept when the name is empty (`[/]`), is a known or parseable style, or matches a tag the same string opened. The last rule is why `[/link]` survives: `link` alone does not parse. `[link=..]a[/link] b[/link]` keeps the first close and escapes the second. An unmatched `[/link]` is escaped.
- **`name=value`.** The first `=` is read as a space, as Rich builds the style string, so `[link=https://x]` is a style and `pkg[feature=on]` is text.
- **Meta tags** (`[@click=...]`) are not styles, so they are escaped.

## Not done, and things to know

- The plan says `[error]FAIL[/error]` is checked "through `capture_ansi`". That helper builds a Rich console with no theme, so the span style `error` never resolves and nothing is coloured, with or without this change. I could not edit `tests/ui/capture.py`, so the two style tests use a local `_themed_ansi` helper in `tests/ui/test_table.py` that builds a console with `RichTheme(theme.as_rich_styles())`. The real `sushicore` console carries that theme already.
- Unchanged old behaviour: a cell with a closing tag that matches nothing but names a Rich style (`[/red]` alone) is kept as a tag, as the plan specifies, and Rich then raises `MarkupError` when the table prints. Not part of this task.
- `_cell` calls `theme.as_rich_styles()` once per cell, as the plan specifies. It builds a 15-entry dict, so the cost is small; it can be hoisted per table later if it matters.
- I did not run any docs checker, and I did not touch the changelog, README, `pyproject.toml` or any `__init__.py`.
- By mistake I ran `git stash` once at the end of a command, then restored everything with `git stash pop` straight away. The working tree is the same as before, with the stash list empty. `git status` afterwards showed the four modified files and the two new ones; the plan file was already modified when I started.

## Orchestrator note

The worker ran `git stash` once, which the repository's git rules forbid in a shared working tree, and restored it at once with `git stash pop`. The orchestrator checked afterwards: the stash list is empty and both working trees hold only the expected changes.
