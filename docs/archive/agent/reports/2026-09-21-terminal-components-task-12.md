# Terminal components, Task 12: four review fixes

Environment: Python 3.13.13, rich 15.0.0, click 8.2.1, typer 0.20.0, pytest 9.1.1, win32.
Baseline: `python -m pytest tests -q` gave `208 passed in 0.67s`. Final: `232 passed in 0.56s`.

## Files changed

- `sushicore/help/from_click.py` (Fix A)
- `tests/help/test_from_click.py` (Fix A model tests, Fix B)
- `tests/help/test_markup_safety.py` (new, Fix A page tests)
- `tests/test_ui_architecture.py` (Fix C)
- `tests/test_typer_help.py` (Fix D, plus one autouse fixture, see "Found wrong")
- `sushicore/ui/probe.py` was created and deleted (Fix C).

## Findings about the brief

1. **`rich_markup_mode` is not always the string `"rich"` on a Typer command.** It is an
   attribute of `TyperCommand` and `TyperGroup` in Typer 0.20 (`typer/core.py` lines 692 and 757).
   But when the app is built as `typer.Typer()` with no mode, the attribute is a
   `typer.models.DefaultPlaceholder` object whose `.value` is `"rich"` (Typer's
   `DEFAULT_MARKUP_MODE`). It is not equal to `"rich"`. With the rule exactly as written
   (`mode == "rich"`), every default Typer app would get its own `\[default: a]` and
   `\[required]` extras escaped a second time and would print a visible backslash. I ran that
   variant: two tests failed (`test_a_typer_app_groups_by_its_panels_and_keeps_typer_help_records`,
   `test_a_typer_app_with_no_mode_set_shows_its_extras_without_a_backslash`). So `_markup` reads
   `getattr(mode, "value", mode)` before comparing, by duck typing, with no Typer import.
   An explicit `rich_markup_mode="rich"` gives the plain string, and a plain Click command gives
   `None`.
2. **Open, not fixed:** a Typer app built with `rich_markup_mode=None` (or `"markdown"`) still
   has Typer escape its extras as `\[default: a]`, and the reader now escapes them again. I ran
   it: the page prints `--kind TEXT  Kind.  \[default: a]`, with the backslash. The brief's rule
   gives this result. Handling it needs a decision (for example unescaping Typer's own
   extras); I left it.
3. **Fix D needs no production change.** The 256-colour branch already worked, so the new tests
   pass on first run. I proved they bite by patching the module in memory (see Fix D).
4. **Rich leaks style state between colour systems.** Rich's shared `Style._add` and
   `Style.parse` caches keep the ANSI codes of the first colour system that rendered a style.
   The new `"256"` test, run before `tests/ui/test_logo.py`, made the truecolour golden test
   fail (`1 failed, 231 passed`). `tests/test_typer_help.py` now clears both caches after each
   test through one autouse fixture. This touches Rich's caches from a test only; production
   uses one colour system per process.
5. The brief's old-tree claim (old grouping test was order-blind) I did not replay against the
   old file; the file is untracked, so there is no old copy. The swap run below shows the new
   test is order-sensitive, and the alphabetical test writes down the difference.

## Fix A: unescaped text reaches Rich

Tests written first. Failing run before the fix (`PYTHONPATH=D:/Projects/sushicore python -m pytest tests/help -q`, filtered to failures):

```
E         - Close with \[/] and \[cyan]x\[/cyan].
E         ?            -        -       -
E         + Close with [/] and [cyan]x[/cyan].
tests\help\test_from_click.py:201: AssertionError
______ test_a_plain_click_argument_help_and_sub_command_help_are_escaped ______
>       assert build_model(hub, ctx).commands[0].entries == (("reset", r"Reset \[hard] mode."),)
E       AssertionError: assert (('reset', 'R...ard] mode.'),) == (('reset', 'R...ard] mode.'),)
E         At index 0 diff: ('reset', 'Reset [hard] mode.') != ('reset', 'Reset \\[hard] mode.')
______________ test_each_command_is_read_in_its_own_markup_mode _______________
E       AssertionError: assert 'Check [b]tools[/b].' == 'Check \\[b]tools\\[/b].'
_____________ test_a_plain_click_option_shows_its_default_marker _____________
E       AssertionError: assert 'Kind.  [default: a]' in 'grow\n\nUsage: grow [OPTIONS]\n\nOptions\n  --kind TEXT  Kind.\n  --help       Show this message and exit.\n'
_ test_a_description_with_a_closing_tag_renders_and_prints_it _
sushicore\help\page.py:38: in render
sushicore\ui\title.py:27: in render
rich\text.py:287: in from_markup
E   rich.errors.MarkupError: closing tag '[/]' at position 11 has nothing to close
_______ test_a_sub_command_short_help_with_a_bracket_prints_as_written ________
E       AssertionError: assert 'Reset [hard] mode.' in 'hub\n\nUsage: hub [OPTIONS] COMMAND [ARGS]...\n\nCommands\n  reset  Reset  mode.\n\nOptions\n  --kind ...
FAILED tests/help/test_from_click.py::test_a_plain_click_option_has_its_default_marker_escaped
FAILED tests/help/test_from_click.py::test_a_plain_click_description_has_its_brackets_escaped
FAILED tests/help/test_from_click.py::test_a_plain_click_argument_help_and_sub_command_help_are_escaped
FAILED tests/help/test_from_click.py::test_each_command_is_read_in_its_own_markup_mode
FAILED tests/help/test_markup_safety.py::test_a_plain_click_option_shows_its_default_marker
FAILED tests/help/test_markup_safety.py::test_a_description_with_a_closing_tag_renders_and_prints_it
FAILED tests/help/test_markup_safety.py::test_a_sub_command_short_help_with_a_bracket_prints_as_written
7 failed, 24 passed in 0.28s
```

After the fix, `_markup(text, owner)` escapes with `rich.markup.escape` unless the owner's mode is
rich. The owning command's mode covers its description and parameters; each child's own mode
covers its short help. Terms and examples are untouched.

```
$ PYTHONPATH=D:/Projects/sushicore python -m pytest tests/help -q
...............................                                          [100%]
31 passed in 0.17s
```

The `[/]` reproduction now renders (`grow` is a plain Click command, `help="Close with [/] once."`,
one option with `show_default=True`):

```
grow
Close with [/] once.

Usage: grow [OPTIONS]

Options
  --kind TEXT  Kind.  [default: a]
  --help       Show this message and exit.
```

## Fix B: grouping test relied on order it did not control

The tree's group is now `_RegistrationOrderGroup(click.Group)` with
`list_commands` returning `list(self.commands)`. Registration order: `init` (Workspace),
`doctor` (none), `add` and `link` (Modules), `secret` (hidden). Expected headings
`["Workspace", "Commands", "Modules"]`, Modules entries `["add", "link"]`. A new test builds
the same tree on a plain `click.Group` and expects `["Modules", "Commands", "Workspace"]`.
The command-with-no-panel and placeholder-panel tests now look sections up by heading; the
placeholder test moved from `doctor` to `add` so it changes something.

Proof the test depends on order: I swapped the `doctor` and `init` registrations in the tree,
ran, then restored the file (`diff` against the saved copy printed `restored`).

```
E       AssertionError: assert ['Commands', ...e', 'Modules'] == ['Workspace',...s', 'Modules']
E         At index 0 diff: 'Commands' != 'Workspace'
FAILED tests/help/test_from_click.py::test_commands_are_grouped_by_panel_in_order_of_first_appearance
FAILED tests/help/test_from_click.py::test_a_placeholder_panel_is_not_a_heading
2 failed, 17 passed in 0.20s
```

After restoring:

```
...................                                                      [100%]
19 passed in 0.15s
```

## Fix C: architecture test ignored `render`'s signature

Added `test_render_takes_exactly_self_and_theme`, parametrised over `K_FILES`, asserting
`list(inspect.signature(component.render).parameters) == ["self", "theme"]`. With
`sushicore/ui/probe.py` (frozen slots dataclass `Probe`, `@final`, `def render(self)`) present:

```
$ PYTHONPATH=D:/Projects/sushicore python -m pytest tests/test_ui_architecture.py -q
E       AssertionError: assert ['self'] == ['self', 'theme']
E         Right contains one more item: 'theme'
FAILED tests/test_ui_architecture.py::test_render_takes_exactly_self_and_theme[probe.py]
1 failed, 48 passed in 0.14s
```

The 48 passes include the five older checks on `probe.py`, which is the gap the review named.
Probe deleted, with its `.pyc`:

```
$ ls sushicore/ui
__init__.py
__pycache__
component.py
definition_list.py
header.py
logo.py
panel.py
table.py
title.py
usage.py
$ PYTHONPATH=D:/Projects/sushicore python -m pytest tests/test_ui_architecture.py -q
...........................................                              [100%]
43 passed in 0.08s
```

## Fix D: the 256-colour gate had no test

`_TerminalConsole(color_system, no_color=False)` now builds its Rich console from its
arguments; `_terminal_app(...)` builds the two-command app on it. New tests: logo shown for
`"256"` and `"truecolor"` (parametrised), hidden for `"standard"`, hidden when `no_color=True`
on a terminal, and the old leaf-page check kept. The old truecolour test became the
parametrised one plus the leaf test.

No failing run exists before a fix, because there is no production change. Instead, in-memory
mutations without touching `typer_help.py`:

```
$ python: t.K_LOGO_COLOUR_SYSTEMS = ("truecolor",); pytest tests/test_typer_help.py
FAILED tests/test_typer_help.py::test_the_root_page_shows_the_logo_on_a_terminal_with_256_colours_or_more[256]
1 failed, 13 passed in 0.14s

$ python: t._logo_visible = lambda raw: raw.is_terminal and raw.color_system is not None
FAILED tests/test_typer_help.py::test_the_root_page_hides_the_logo_on_a_standard_colour_terminal
FAILED tests/test_typer_help.py::test_the_root_page_hides_the_logo_when_colour_is_switched_off_on_a_terminal
2 failed, 12 passed in 0.15s
```

Unmutated: `14 passed in 0.19s` for the file.

## Verification

Syntax check:

```
$ python -m py_compile sushicore/help/from_click.py tests/help/test_from_click.py tests/help/test_markup_safety.py tests/test_ui_architecture.py tests/test_typer_help.py; echo "exit $?"
exit 0
```

`py_compile` printed no output. Full suite:

```
$ PYTHONPATH=D:/Projects/sushicore python -m pytest tests -q
........................................................................ [ 93%]
................                                                         [100%]
232 passed in 0.56s
```

Before the style-cache fixture, the same command gave `1 failed, 231 passed`
(`tests/ui/test_logo.py::test_the_logo_matches_its_golden_file`); that failure is finding 4.
No line in the files I wrote is longer than 100 characters (`awk` printed nothing). The
probe is gone (listing above).

## Not done

- No commit, and no edits to `pyproject.toml`, READMEs, changelog, specs, plans or any `__init__.py`.
- The spec's Help paragraph already states the escape rule; it does not mention the
  `DefaultPlaceholder` unwrapping (finding 1). Someone with the spec should add it.
- Finding 2 (Typer with `rich_markup_mode=None` prints a visible backslash) is open.
- `tools/documentation/check_source_comments.py` does not exist in this repository, so the
  comment shape was checked by reading only.
- `git status` still shows `README.md`, `docs/README.md`, `docs/reference/CHANGELOG.md`,
  `pyproject.toml`, `sushicore/console.py`, `sushicore/renderer.py`, `sushicore/theme.py` as
  modified, and `sushicore/ui/logo.py` changed at 22:10 while I worked. None of those are mine.
