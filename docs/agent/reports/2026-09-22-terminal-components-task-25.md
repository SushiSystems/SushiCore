# Task 25 — the help screen on Typer 0.27, and no more `click` in `tests/test_typer_help.py`

## Files changed

- `sushicore/ui/definition_list.py` — entry text goes through `escape_unknown_tags`.
- `sushicore/ui/title.py` — the description goes through `escape_unknown_tags`.
- `tests/ui/test_definition_list.py` — four tests added.
- `tests/ui/test_title.py` — four tests added, and a `_painted` helper for the colour check.
- `tests/help/test_from_click.py` — the Typer context comes from the command; the Typer test split
  in two and relaxed to what both versions hand out.
- `tests/help/test_markup_safety.py` — `_typer_leaf` builds its contexts with `make_context`.
- `tests/test_typer_help.py` — `import click` gone, one test added, two reworked.

Nothing else was touched. `pyproject.toml`, the changelog, the plan, the specs, every `__init__.py`
and `sushicore/typer_help.py` are as the orchestrator left them.

## What the two Typer versions differ on

Both environments run Rich 15.0.0. The current one has Typer 0.20.0 with Click 8.2.1, `ci_venv`
has Typer 0.27.2 with Click 8.5.0. Read off the records the reader got from the same app:

| | 0.20.0 | 0.27.2 |
| --- | --- | --- |
| argument term | `MODULE` | `module` |
| option metavar | `--kind TEXT` | `--kind <str>` |
| usage piece | `tool grow [OPTIONS] MODULE` | `tool grow [OPTIONS] {module}` |
| required extra | `The module.  \[required]` | `The module.  [required]` |
| default extra | `Kind [x].  \[default: a]` | `Kind [x].  [default: a]` |

The escaping is the defect: 0.27 hands the extras over plain, `DefinitionList` read them as Rich
markup, and `[required]` and `[default: a]` were dropped from the page.

The `Context` class is the other difference. From 0.27 on, Typer carries its own copy of Click
under `typer/_click/` and no longer installs the `click` package, so a context built with
`click.Context` is not the class the Typer command expects. Tests that drive a Typer command now
build the context from the command itself, `command.make_context(name, [], parent=...,
resilient_parsing=True)`, which works unchanged on 0.20. Tests that drive a plain Click command
keep `import click` and `click.Context`; that is `tests/help/test_from_click.py` and
`tests/help/test_markup_safety.py`.

No test carries a version check. The two places where the versions genuinely disagree are matched
case-insensitively (the argument name) or with the escaping backslash removed (the extras), and
each is marked with a one-line comment.

## Reproducing, before anything was changed

```
$ PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=D:/Projects/sushicore ci_venv/Scripts/python.exe \
    -m pytest tests -q -p no:cacheprovider
FAILED tests/help/test_from_click.py::test_a_typer_app_groups_by_its_panels_and_keeps_typer_help_records
FAILED tests/help/test_markup_safety.py::test_a_typer_app_in_rich_mode_shows_its_required_and_default_extras_without_a_backslash
FAILED tests/help/test_markup_safety.py::test_a_typer_app_with_no_mode_set_shows_its_extras_without_a_backslash
FAILED tests/test_typer_help.py::test_leaf_help_lists_arguments_options_and_examples
4 failed, 395 passed in 1.44s
```

The same four in the current environment pass:

```
$ PYTHONPATH=D:/Projects/sushicore python -m pytest \
    "tests/help/test_from_click.py::test_a_typer_app_groups_by_its_panels_and_keeps_typer_help_records" \
    tests/help/test_markup_safety.py \
    "tests/test_typer_help.py::test_leaf_help_lists_arguments_options_and_examples" \
    -q -p no:cacheprovider
........                                                                 [100%]
8 passed in 0.20s
```

The failure that names the defect:

```
>       assert "The module.  [required]" in text
E       AssertionError: assert 'The module.  [required]' in 'tool grow\nPaint x here.\n\nUsage: tool grow [OPTIONS] {module}\n\nArguments\n  module  The module.\n\nOptions\n  --kind <str>  Kind.\n  --help        Show this message and exit.\n'
```

## The component tests, written first and seen failing

```
$ PYTHONPATH=D:/Projects/sushicore python -m pytest tests/ui/test_title.py tests/ui/test_definition_list.py -q -p no:cacheprovider
....F.....F........                                                      [100%]
    def test_an_unescaped_extra_marker_stays_in_the_description():
        title = Title("hub add", "Bring a module in.  [required]")
>       assert capture(title) == "hub add\nBring a module in.  [required]\n"
E       AssertionError: assert 'hub add\nBri... module in.\n' == 'hub add\nBri... [required]\n'
E           hub add
E         - Bring a module in.  [required]
E         + Bring a module in.
    def test_an_unescaped_extra_marker_stays_on_the_page():
        text = capture(DefinitionList("Arguments", (("module", "The module.  [required]"),)))
>       assert "The module.  [required]" in text
E       AssertionError: assert 'The module.  [required]' in 'Arguments\n  module  The module.\n'
FAILED tests/ui/test_title.py::test_an_unescaped_extra_marker_stays_in_the_description
FAILED tests/ui/test_definition_list.py::test_an_unescaped_extra_marker_stays_on_the_page
2 failed, 17 passed in 0.13s
```

After the change, with the architecture test that guards the allowed imports:

```
$ PYTHONPATH=D:/Projects/sushicore python -m pytest tests/ui/test_title.py tests/ui/test_definition_list.py tests/test_ui_architecture.py -q -p no:cacheprovider
..............................................................           [100%]
62 passed in 0.20s
```

## The page on a hub-like tree

A group with `rich_markup_mode="rich"`, an `add` command carrying a required argument, an option
with a default and an option whose help text holds `[cyan]build/hub[/cyan]`, printed at 78 columns
through `help_group`, run in `ci_venv`:

```
hub add
Bring a module in.

Usage: hub add [OPTIONS] {module}

Arguments
  module  The module.  [required]

Options
  --type <str>  Build into build/hub.  [default: debug]
  --dry-run     Show the plan only.
  --help        Show this message and exit.

Examples
  hub add sr  bring sushiruntime in
```

The same script on Typer 0.20 prints `MODULE`, `--type TEXT` and `[OPTIONS] MODULE`, and the same
`[required]` and `[default: debug]`.

## `Title` and `DefinitionList` on the four kinds of bracket

Run in `ci_venv`, one line per component:

```
--- style tag: 'Build into [cyan]build/hub[/cyan].'
Title     : 'Build into build/hub.'
List      : '  --type  Build into build/hub.'
--- stray bracket: 'Reset [hard] mode.'
Title     : 'Reset [hard] mode.'
List      : '  --type  Reset [hard] mode.'
--- required: 'The module.  [required]'
Title     : 'The module.  [required]'
List      : '  --type  The module.  [required]'
--- escaped: 'Kind.  \[default: debug]'
Title     : 'Kind.  [default: debug]'
List      : '  --type  Kind.  [default: debug]'
```

A legitimate style tag is still a tag and still paints: the same title through a truecolour console
gives `'Build into \x1b[36mbuild/hub\x1b[0m.'`. A stray unknown bracket is kept as text. A marker
that Typer already escaped shows its brackets once, not twice. Both components pass the theme's own
style names in, so `[success]…[/success]` stays a tag as it does in a table cell.

## Suite counts

Current environment, Typer 0.20.0, Click 8.2.1, default order and reversed:

```
$ PYTHONPATH=D:/Projects/sushicore python -m pytest tests -q -p no:cacheprovider
409 passed in 1.03s
$ PYTHONPATH=D:/Projects/sushicore python -m pytest $(ls tests/test_*.py | sort -r) tests/ui tests/help -q -p no:cacheprovider
409 passed in 1.17s
```

`ci_venv`, Typer 0.27.2, Click 8.5.0, the same two orders:

```
$ PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=D:/Projects/sushicore ci_venv/Scripts/python.exe -m pytest tests -q -p no:cacheprovider
409 passed in 1.13s
$ PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=D:/Projects/sushicore ci_venv/Scripts/python.exe -m pytest $(ls tests/test_*.py | sort -r) tests/ui tests/help -q -p no:cacheprovider
409 passed in 1.10s
```

Syntax check of every file written:

```
$ python -m py_compile sushicore/ui/definition_list.py sushicore/ui/title.py tests/ui/test_definition_list.py tests/ui/test_title.py tests/help/test_from_click.py tests/help/test_markup_safety.py tests/test_typer_help.py; echo "exit $?"
exit 0
```

No line in the seven files runs past 100 columns (`awk 'length>100'` printed nothing). The
repository carries no `tools/` checker to run.

## Departures from the plan, and what was left undone

- The plan asks for the raw-record test to assert what the screen shows.
  `tests/help/test_from_click.py` tests the reader, not the page, so it still asserts on the model;
  the page assertions live in `tests/help/test_markup_safety.py` and `tests/test_typer_help.py`,
  where the extras and the absence of a backslash are checked on rendered text. If the orchestrator
  wants the reader test moved onto a page too, say so and it moves.
- `test_a_typer_app_groups_by_its_panels_and_keeps_typer_help_records` covered two behaviours, so it
  is now `test_a_typer_app_groups_by_its_panels` and
  `test_a_typer_leaf_keeps_the_help_records_typer_hands_out`.
- `test_looking_a_child_up_twice_leaves_it_with_one_help_page` also built its contexts with
  `click.Context`. It was not on the plan's list of four, and it did not fail on 0.27, but dropping
  `import click` from the module forced it over to `make_context` as well.
- The suite went from 399 tests to 409: nine added (four on `Title`, four on `DefinitionList`, one
  on the leaf page's extras) and one split into two. The 399 is the collection count of the
  `ci_venv` baseline run above, 4 failed plus 395 passed.
- Nothing was installed or upgraded, nothing was committed, and no environment was changed.

## One thing in the plan that does not hold

The plan's Task 21 text says a parse that raises `rich.errors.ColorParseError` must count as "not a
style". `sushicore/markup.py` catches `StyleSyntaxError` alone. That is correct for Rich 15, because
`Style.parse` wraps a `ColorParseError` in a `StyleSyntaxError` before it leaves, so the behaviour is
right and no test is missing; the plan's sentence is just wider than the code. I left `markup.py`
alone — it is not one of my files.
