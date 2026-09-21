# Task 15 — choose the logo and wire it into the page

Worker report. Plan: `docs/agent/plans/2026-09-21-terminal-components.md`, Wave 6b, Task 15 with
its amendments from the second review.

## Files changed

- Created `sushicore/help/logo_choice.py`: `choose_logo(*, width, dark_background) -> Logo | None`.
- Modified `sushicore/help/page.py`: `HelpPage.logo: Component | None = None` in place of
  `show_logo: bool`; the module and class docstrings lost their evaluative tails (review 2.4).
- Modified `sushicore/typer_help.py`: the guard, the logger, the logo choice, and the module
  docstring (review 2.3).
- Created `tests/help/test_logo_choice.py`: 11 cases.
- Modified `tests/help/test_page.py`: the three `show_logo` tests rewritten, one added for the
  logo's place in the stack, docstrings on `_leaf` and `_root` (review 2.6).
- Modified `tests/test_typer_help.py`: the Rich style-cache fixture removed, the terminal tests
  rewritten around `Logo(...).width`, six cases added for the guard, docstrings on `_app` and
  `_run` (review 2.6).

Not touched: `sushicore/ui/logo.py`, `tests/ui/test_logo.py`, the goldens, any `__init__.py`,
`pyproject.toml`, the changelog, the specs and the plans. Nothing committed.

## What the guard does

`HelpGroup.console_provider` now defaults to `None`. Every help call, for the group and for each
child, goes through `_write_guarded`, which logs one warning through
`logging.getLogger("sushicore.help")` and hands over to Typer when the provider is missing, the
provider raises, or building or drawing the page raises any `Exception`. The hand-over is
`TyperGroup.format_help(self, ctx, formatter)` for the group and
`type(command).format_help(command, ctx, formatter)` for a child. A child's wrapper is an instance
attribute, so `type(command).format_help` reaches Typer's own method and cannot recurse; the test
`test_a_child_whose_provider_raises_falls_back_to_typers_help` passes, which a recursion would not
allow.

`_write_page` builds the whole page before its single `formatter.write`, so a failure leaves the
formatter untouched and the fallback screen is whole.

## The `[/]` case: the plan asks for something Typer cannot do

The plan's acceptance criterion says a `[/]` in a `rich` docstring must leave `--help` at exit 0
with Typer's own screen. It does not, and sushicore is not the reason. Under
`rich_markup_mode="rich"`, Typer 0.20's own help renderer raises the same
`rich.errors.MarkupError` on the same input, with no sushicore in the process:

```
$ python scratchpad/probe_markup.py
=== root help 'Manage [/] the stack.' exit 1 MarkupError
=== leaf help exit 1 MarkupError
=== root help 'Manage the stack.' exit 1 MarkupError
=== leaf help exit 1 MarkupError
```

The third line is a root app whose own help text is clean and whose `doctor` command carries the
`[/]`: Typer parses every child's short help to draw the root screen, so the root dies too.

So the guard catches the page's `MarkupError`, logs one warning, hands over, and Typer then raises
the identical error. Review finding 3.4 reads as a sushicore defect; it is a Typer one that
sushicore inherits. Falling back to Typer cannot fix it. Two ways out, both outside this task's
files and both a decision for the owner:

1. A second fallback to `click.Command.format_help`, which is plain Click and parses no markup.
   Typer's rich renderer writes to stdout directly, so its partial screen would already be out
   before the plain one follows, and the call would log two warnings, not one.
2. Make the page tolerate bad markup: `Title` and `DefinitionList` fall back to literal text when
   `Text.from_markup` raises. That keeps sushicore's own screen and never reaches Typer, and it
   touches `sushicore/ui/`, which Task 15 may not write.

I implemented what the plan says and pinned the measured truth in two tests:
`test_a_stray_close_tag_in_rich_help_is_logged_and_handed_to_typers_help` asserts the one warning
and that what escapes is the renderer's `MarkupError`, and
`test_typer_alone_fails_on_the_same_stray_close_tag` records that vanilla Typer fails identically,
so the day Typer fixes it the second test turns red and says so.

## Verification

### The tests fail first

New module missing:

```
$ python -m pytest tests/help/test_logo_choice.py tests/help/test_page.py tests/test_typer_help.py -q -p no:randomly
=================================== ERRORS ====================================
_______________ ERROR collecting tests/help/test_logo_choice.py _______________
ImportError while importing test module 'D:\Projects\sushicore\tests\help\test_logo_choice.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
C:\ProgramData\Miniconda\Lib\importlib\__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\help\test_logo_choice.py:5: in <module>
    from sushicore.help.logo_choice import choose_logo
E   ModuleNotFoundError: No module named 'sushicore.help.logo_choice'
=========================== short test summary info ===========================
ERROR tests/help/test_logo_choice.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.20s
```

The other two files, before `page.py` and `typer_help.py` changed:

```
$ python -m pytest tests/help/test_page.py tests/test_typer_help.py -q -p no:randomly
=========================== short test summary info ===========================
FAILED tests/help/test_page.py::test_a_root_page_draws_the_logo_it_is_given
FAILED tests/help/test_page.py::test_the_logo_comes_before_the_title - TypeEr...
FAILED tests/help/test_page.py::test_the_logo_never_shows_on_a_sub_command_page
FAILED tests/test_typer_help.py::test_a_dark_terminal_draws_the_lockup_with_its_glow
FAILED tests/test_typer_help.py::test_a_console_too_narrow_for_the_wordmark_draws_the_mark_alone
FAILED tests/test_typer_help.py::test_a_console_narrower_than_the_mark_draws_no_logo
FAILED tests/test_typer_help.py::test_a_group_whose_provider_raises_falls_back_to_typers_help
FAILED tests/test_typer_help.py::test_a_child_whose_provider_raises_falls_back_to_typers_help
FAILED tests/test_typer_help.py::test_a_help_group_used_without_a_provider_falls_back_to_typers_help
FAILED tests/test_typer_help.py::test_a_stray_close_tag_in_rich_help_falls_back_to_typers_help
FAILED tests/test_typer_help.py::test_each_help_call_logs_one_warning_of_its_own
11 failed, 19 passed in 0.32s
```

`test_a_light_terminal_draws_the_lockup_without_a_glow` passed before the change, because the old
code drew `Logo()` with no glow on any qualifying terminal. It is in the file for the pair with
the dark case.

### The tests pass after

```
$ python -m pytest tests/help/test_logo_choice.py tests/help/test_page.py tests/test_typer_help.py -q -p no:randomly
..........................................                               [100%]
42 passed in 0.26s
```

### The whole suite

```
$ python -m pytest tests -q -p no:randomly
........................................................................ [ 22%]
........................................................................ [ 45%]
........................................................................ [ 67%]
........................................................................ [ 90%]
..............................                                           [100%]
318 passed in 11.23s
```

The 256-colour terminal test placed before the logo goldens, which is what the style cache used to
break:

```
$ python -m pytest tests/test_typer_help.py tests/ui -q -p no:randomly
........................................................................ [ 96%]
...                                                                      [100%]
75 passed in 3.04s
```

Twice in the default (random) order, after the fixture was removed from `tests/test_typer_help.py`:

```
$ python -m pytest tests -q
318 passed in 11.05s
$ python -m pytest tests -q
318 passed in 10.43s
```

### Syntax check and line length

```
$ python -m py_compile sushicore/help/logo_choice.py sushicore/help/page.py sushicore/typer_help.py tests/help/test_logo_choice.py tests/help/test_page.py tests/test_typer_help.py; echo "exit $?"
exit 0
$ awk 'length>100 {print FILENAME": "FNR": "length}' <the same six files>; echo "long-lines exit $?"
long-lines exit 0
```

## What a user sees

A fake 80-column truecolour terminal with `dark_background = True`, colour codes stripped for this
report. Root:

```
========== hub --help
     ▄▄▀▀▀▀▀▀▀▀▄       ▄▄▄▄ ▄▄ ▄▄  ▄▄▄▄ ▄▄ ▄▄ ▄▄
   ▄▀▀▀▀▀▀▀▀▀██▀▀▄    ▀█▄▄  ██ ██ ▀█▄▄  ██▄██ ██
  ▄▀▀██▀▀▀▀▀██▀████      ██ ██ ██    ██ ██▀██ ██
  ███████████▀██████  ▀▀▀▀   ▀▀▀  ▀▀▀▀  ▀▀ ▀▀ ▀▀
  ██████████████████   ▄▄▄▄ ▄▄ ▄▄  ▄▄▄▄ ▄▄▄▄▄ ▄▄▄▄▄ ▄▄▄ ▄▄▄  ▄▄▄▄
  █████▀▀██▀▀████▀▀▀  ▀█▄▄  ▀█▄█▀ ▀█▄▄    █   ██▄▄  ███████ ▀█▄▄
   ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀       ██   █      ██   █   ██    ██ ▀ ██    ██
     ▀▀▀▀▀▀▀▀▀▀▀      ▀▀▀▀    ▀   ▀▀▀▀    ▀   ▀▀▀▀▀ ▀▀   ▀▀ ▀▀▀▀

hub
One tree for the stack.

Usage: hub [OPTIONS] COMMAND [ARGS]...

Modules
  add  Bring one or more stack modules into the workspace.

Commands
  doctor  Check the tools the stack needs.

Desktop app
  gui  The desktop application.

Options
  --install-completion  Install completion for the current shell.
  --show-completion     Show completion for the current shell, to copy it or
                        customize the installation.
  --help                Show this message and exit.
```

Leaf:

```
========== hub add --help
hub add
Bring one or more stack modules into the workspace.

Usage: hub add [OPTIONS] MODULE

Arguments
  MODULE  The module to bring in.  [required]

Options
  --dry-run  Show the plan only.
  --help     Show this message and exit.

Examples
  hub add sr  bring sushiruntime in
```

The halo rows around the roll are the glow; with `dark_background = False` they are blank, which is
what `test_a_light_terminal_draws_the_lockup_without_a_glow` compares against.

The `Options` rows still carry trailing spaces out to the second column's width. That is review
finding 4, `Padding(expand=False)`, and it belongs to Task 16's `definition_list.py`, not here.

## Not done

- No width is written as a number anywhere in the code or the tests. Every one comes from
  `Logo(...).width`, so Task 17 can change the mark's size without touching these files.
- `sushicore/help/__init__.py` does not re-export `choose_logo`; the orchestrator owns that file.
- No changelog line, no README or spec edit, no commit.
- The spec's "Help" section still says `page.py` draws the logo "when asked" and the "logo's
  visibility" section still names `show_logo`. Both are now wrong by one word; the orchestrator
  owns the spec.
- `HelpPageError` is new public surface in `sushicore/typer_help.py`. The plan does not name it;
  raising it is how the missing provider reaches the one `except` without a bare `Exception`. Say
  the word and it becomes a private `_HelpPageError`.
