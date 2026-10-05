# sushicore.help

A help screen as data, and the page that lays it out from `sushicore.ui` components.
`sushicore/typer_help.py`, beside this folder, wires the page into a Typer application.

## What it owns

| Name | File | Does |
| --- | --- | --- |
| `HelpModel`, `HelpSection` | `model.py` | Hold one help screen: title, usage, command groups, arguments, options, examples |
| `build_model` | `from_click.py` | Reads a Click or Typer command into a `HelpModel` |
| `HelpPage` | `page.py` | Lays a model out as logo, title, usage, then each list that has rows |
| `choose_logo` | `logo_choice.py` | Returns the widest logo that fits a console, or none |

## What it depends on

`sushicore.ui` for the components and `sushicore.theme`. `from_click.py` reads the attributes of
Click's command objects and imports neither Click nor Typer.

## Using it

```python
import typer
from sushicore.typer_help import help_group

app = typer.Typer(cls=help_group(provider), rich_markup_mode="rich")
```

`provider` returns the CLI's `Console`, the object `LazyConsole.get()` builds, not the
`LazyConsole` itself. It is called when help is drawn, not at import, so `--help` runs outside a
workspace. Pass the same class to every `add_typer` sub-application; one without it keeps
Typer's own screen.

## What the page shows

Commands are grouped by Typer's `rich_help_panel`, in the order each panel first appears; a
command with none lands under `Commands`. Examples come from a command's `epilog`, one per
line, written as `command  # note`.

The logo prints on the root page only, and only on a UTF-8 terminal with colour on and 256
colours or more. `choose_logo` takes the mark with `SUSHI SYSTEMS` beside it when the console is
at least 72 columns wide (68 without the glow), the mark alone when only that fits (20 columns
with the glow, 16 without), and nothing below that.

On a dark terminal the mark gets a white glow. The decision comes from the `[cli] background`
setting and, when that is `auto`, from `COLORFGBG`; without either the glow stays off, so a
light terminal keeps its look. Windows Terminal does not set the variable, so a CLI's config
says it once:

```toml
[cli]
background = "dark"   # auto | dark | light
```

`SUSHI_CLI_BACKGROUND` sets the same thing from the environment.

## How the page is printed

The page is printed on the console's Rich stream, the way Typer prints its own help, and not
through Click's `echo`: on Windows Click wraps its output in colorama, which cannot read
true-colour codes. `ctx.get_help()` therefore returns an empty string for a command that draws
its page.

A classic Windows console (`cmd`, a PowerShell window) starts a program with virtual terminal
processing off, and Rich then draws 16 colours. Building a `RichRenderer` turns that mode on for
stdout and stderr, so true colour and the logo work there too.

If drawing the page fails, `--help` logs one warning under the logger `sushicore.help` and shows
Typer's own screen.

## Known limits

- Typer turns an application with one command and no callback into a plain command, so the
  group never sees it and Typer's own screen stays.
- An application built with `rich_markup_mode=None` or `"markdown"` prints a backslash before the
  bracketed extras Typer adds to a parameter, such as `\[default: a]`. `"rich"` and Typer's
  default mode are correct.
- Under `rich_markup_mode="rich"` a stray `[/]` in a command's help raises `MarkupError` in
  Typer itself, for the whole root screen. `help_group` logs its warning and hands over to
  Typer, which raises the same error, so `--help` still fails for that input.

The design is archived as `docs/archive/agent/specs/2026-09-21-terminal-components-design.md`.
