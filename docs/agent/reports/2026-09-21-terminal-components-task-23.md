# Task 23 — print the help page through Rich, not through Click's `echo`

Date: 2026-09-22. Plan: `docs/agent/plans/2026-09-21-terminal-components.md`, Task 23.

## Files changed

- `sushicore/typer_help.py`
- `tests/test_typer_help.py`
- `docs/agent/reports/2026-09-21-terminal-components-task-23.md` (this report)

Nothing else was touched. `sushicore/windows_console.py`, `sushicore/renderer.py`,
`tests/test_windows_console.py` and `tests/test_renderer_components.py` belong to Task 22 and
were only read, never written.

## The cause, reproduced

The plan's explanation holds. Two measurements.

First, colorama 0.4.6 reads a true-colour sequence as a list of separate SGR parameters. A fake
stream whose `isatty()` returns true, wrapped with `AnsiToWin32(convert=True, strip=False)`, with
`call_win32` replaced by a recorder:

```
input : '\x1b[38;2;240;165;0mX\x1b[0m\x1b[38;2;26;28;32mY\x1b[0m'
output: 'XY'
win32 : ('m', (38, 2, 240, 165, 0))
win32 : ('m', (0,))
win32 : ('m', (38, 2, 26, 28, 32))
win32 : ('m', (0,))
```

The escape sequences never reach the stream; each parameter is handed to `call_win32`, which
(`colorama/ansitowin32.py:238`) loops over the parameters and runs whichever ones it recognises.
Asking the converter's own `win32_calls` map what each parameter of the two sequences does:

```
38 -> not in win32_calls (ignored)
2 -> ('style', (0,))
240 -> not in win32_calls (ignored)
165 -> not in win32_calls (ignored)
0 -> ('reset_all', ())
26 -> not in win32_calls (ignored)
28 -> not in win32_calls (ignored)
32 -> ('fore', (2,))
```

So amber `38;2;240;165;0` becomes dim plus a full reset, which is the light grey the owner saw,
and nori `38;2;26;28;32` becomes dim plus foreground 2, green. That is the screenshot.

Second, the owner's Typer 0.27.2 does wrap its output with colorama. In
`C:/Users/sushi/pipx/venvs/sushihub/Lib/site-packages/typer/_click/_compat.py:459-488`:

```
# On Windows, wrap the output streams with colorama to support ANSI
# color codes.
...
    def auto_wrap_for_ansi(stream: TextIO, color: bool | None = None) -> TextIO:
        ...
        import colorama
        strip = should_strip_ansi(stream, color)
        ansi_wrapper = colorama.AnsiToWin32(stream, strip=strip)
```

and the route into it is `typer/_click/decorators.py:44-48`, `echo(ctx.get_help(), color=ctx.color)`,
with `Command.get_help` (`typer/_click/core.py:618`) returning `formatter.getvalue()`. Writing the
page into the formatter therefore sent it through `echo`, and through colorama.

## What I verified only by reading, because Typer 0.27 does not run here

The tests run against typer 0.20.0 with click 8.2.1 (conda env). The owner's pipx venv has typer
0.27.2 with its vendored `typer/_click/` and click 8.5.0. I read the 0.27.2 sources for the three
shapes `typer_help.py` depends on:

- `TyperGroup.format_help(self, ctx, formatter)` — `typer/core.py:1208`, same signature, so
  `partial(TyperGroup.format_help, self)` still binds the fallback. `TyperCommand.format_help` at
  `typer/core.py:975` gives `type(command).format_help` the same shape for a leaf.
- `TyperGroup.get_command(self, ctx, cmd_name)` — `typer/core.py:1044`, returns
  `self.commands.get(cmd_name)`, so `super().get_command(...)` in `HelpGroup` resolves and the
  child object it hands back is the cached one, which is what the "one help page" test relies on.
  In 0.27 `TyperGroup` derives from the vendored `_click.Command` rather than `click.Group`; the
  annotations in `typer_help.py` are strings under `from __future__ import annotations` and are
  never evaluated, so the change of base class does not reach them.
- The `--help` callback — `typer/_click/decorators.py:44`, still `echo(ctx.get_help())`, and
  `get_help` still `format_help(ctx, formatter); return formatter.getvalue().rstrip("\n")`. With the
  formatter untouched, `--help` prints one empty line after the page. This is the one behaviour I
  could not run on 0.27; on 0.20 the same code path is exercised by the tests.

## What changed in the code

`_write_page` became `_print_page(command, ctx, console)`: it builds the model and the page as
before and prints with `console.console.print(page.render(console.theme))`. `_draw`, the `io`
import and the now-unused `Theme` import are gone. `_write_guarded` keeps the formatter, because
the Typer fallback still writes into it. The logo gate and `_logo_for` are unchanged.

One deviation from the plan's wording: the plan gives the signature
`_write_page(command, ctx, formatter, console)`, but nothing in the new body reads `formatter`. I
dropped the parameter rather than carry a dead argument; the guard still passes the formatter to
Typer's own help. Say the word and I will put it back.

The module docstring gained the sentence about `ctx.get_help()` returning an empty string. Three
docstrings that said "into the formatter" now say what the function does.

## Tests

Written first, run against the old code, 13 failed for the stated reason — the page was in
`result.output`, not on the stand-in console's stream:

```
FAILED tests/test_typer_help.py::test_root_help_groups_commands_under_their_panels
FAILED tests/test_typer_help.py::test_leaf_help_lists_arguments_options_and_examples
FAILED tests/test_typer_help.py::test_a_sub_group_draws_its_own_page_not_a_leaf_page
FAILED tests/test_typer_help.py::test_a_leaf_below_a_sub_group_draws_a_page
FAILED tests/test_typer_help.py::test_a_command_with_no_panel_lands_under_commands
FAILED tests/test_typer_help.py::test_the_click_formatter_is_left_empty_for_a_page_drawing_group
FAILED tests/test_typer_help.py::test_looking_a_child_up_twice_leaves_it_with_one_help_page
FAILED tests/test_typer_help.py::test_the_root_page_shows_the_logo_on_a_terminal_with_256_colours_or_more[256]
FAILED tests/test_typer_help.py::test_the_root_page_shows_the_logo_on_a_terminal_with_256_colours_or_more[truecolor]
FAILED tests/test_typer_help.py::test_the_page_reaches_a_truecolour_terminal_with_the_rolls_own_colour_codes
FAILED tests/test_typer_help.py::test_a_dark_terminal_draws_the_lockup_with_its_glow
FAILED tests/test_typer_help.py::test_a_light_terminal_draws_the_lockup_without_a_glow
FAILED tests/test_typer_help.py::test_a_console_too_narrow_for_the_wordmark_draws_the_mark_alone
13 failed, 14 passed in 0.35s
```

`_run` and the new `_terminal_page` read the page from the stand-in console's own stream. Every
assertion about content, grouping, examples, the logo gate and the guard is kept. Three tests are
new:

- `test_the_page_reaches_a_truecolour_terminal_with_the_rolls_own_colour_codes` — the page on a
  fake true-colour terminal holds `38;2;240;165;0` and `38;2;26;28;32`.
- `test_the_click_formatter_is_left_empty_for_a_page_drawing_group` — `CliRunner`'s output for a
  page-drawing group is blank.
- `test_a_block_that_fails_to_draw_leaves_no_part_of_the_page_on_the_console` — a stand-in page
  whose renderable is `Group(Text("the block that drew"), _Exploding())`, where `_Exploding`
  raises in `__rich_console__`. The console's stream stays empty and Typer's own screen appears.

Before writing that test I checked the claim on its own:

```
raised: the second block cannot be drawn
stream: ''
```

## Commands and their output

```
$ python -m py_compile sushicore/typer_help.py tests/test_typer_help.py; echo "exit $?"
exit 0
```

```
$ PYTHONPATH=D:/Projects/sushicore python -m pytest tests/test_typer_help.py -q
...........................                                              [100%]
27 passed in 0.25s
```

```
$ PYTHONPATH=D:/Projects/sushicore python -m pytest tests -q
........................................................................ [ 18%]
........................................................................ [ 36%]
........................................................................ [ 55%]
........................................................................ [ 73%]
........................................................................ [ 92%]
..............................                                           [100%]
390 passed in 1.36s
```

```
$ PYTHONPATH=D:/Projects/sushicore python -m pytest $(ls tests/test_*.py | sort -r) tests/ui tests/help -q
........................................................................ [ 18%]
........................................................................ [ 36%]
........................................................................ [ 55%]
........................................................................ [ 73%]
........................................................................ [ 92%]
..............................                                           [100%]
390 passed in 1.27s
```

Task 22's tests were green in both runs. `PYTHONIOENCODING=utf-8` was set on the pytest and
scratch runs, because this shell's stdout is cp1252 and the block characters would not encode.

## Not done

- Nothing committed; no edit to `pyproject.toml`, `README.md`, `docs/README.md`,
  `docs/reference/CHANGELOG.md`, the spec, the plan or any `__init__.py`.
- The spec's "Help" paragraph and `docs/README.md`'s "Help screens" still describe the old route
  through Click's formatter. The plan assigns both to the orchestrator.
- Nothing was run on Typer 0.27.2 or against a real Windows console; the 0.27 claims above come
  from reading its sources, and `sushicore/windows_console.py` from Task 22 is what turns VT on.
- No `tools/documentation/check_source_comments.py` exists in this repository, so the comment
  rules were applied by hand, not checked by a tool.
