# sushicore

Shared, config-driven CLI presentation layer for the Sushi* developer CLIs
(`sr` / sushiruntime, `se` / sushiengine, `hub` / sushistack). One seam for
colors, icons, and output formatting so a visual change (e.g. "I want
different CLI colors") is a config edit in one place, not a hunt through
three hardcoded `console.py` files.

## Design

Small, swappable pieces (SOLID), not one monolith:

- `Theme` (`sushicore.theme`) — pure data: style tokens (`info`, `success`,
  `warn`, `error`, `cmd`, `header`, `panel_border`, `muted`). Presets: `default`,
  `mono`, `muted`. Register your own with `register_theme(name, Theme(...))`.
- `IconSet` (`sushicore.icons`) — pure data: the prefix/glyph printed before a
  line. Presets: `text` (`[INFO]`, ...), `emoji`, `minimal`, `none`.
  Register your own with `register_icon_set(...)`.
- `Renderer` (`sushicore.renderer`) — a `Protocol` of eight methods describing
  how a themed message gets drawn: `line`, `command`, `header`, `panel`,
  `table`, `progress`, `result`, `prompt`. `RichRenderer` is the default
  (colored, via Rich, or with ANSI stripped for `NO_COLOR`, `color = "never"`
  and a non-TTY stream); `PlainRenderer` writes markup-free text;
  `JsonRenderer` writes one JSON event per line for a program to read. Any
  object implementing the same eight methods is a drop-in replacement.
- `Console` (`sushicore.console`) — the facade every CLI actually calls
  (`console.info(...)`, `console.error(...)`, ...). It only translates
  semantic calls into renderer calls using a theme + icon set; it never picks
  a color itself.
- `ui` (`sushicore.ui`) — one file per terminal element: `Logo`, `Header`,
  `Panel`, `Table`, `Title`, `Usage`, `DefinitionList`. Each is a frozen
  dataclass with `render(theme)`, and each reads only `Theme` and `brand`.
  `RichRenderer.table`, `panel` and `header` draw through them.
- `help` (`sushicore.help`) — a help screen as data (`HelpModel`, built from
  a Click command by `build_model`) and the `HelpPage` that lays it out from
  `ui` components.
- `build_console()` (`sushicore.__init__`) — the factory that wires the above
  together from layered config. This is the one function a CLI needs to call.

Themes and icon sets are pure data, so most customization needs **no code at
all** — just a config file.

## Help screens

A Typer CLI gets the themed help screen with one argument:

```python
app = typer.Typer(cls=help_group(provider), rich_markup_mode="rich")
```

`provider` returns the CLI's `Console`, the object `LazyConsole.get()` builds, not
the `LazyConsole` itself. It is called when help is drawn, not at import, so
`--help` runs outside a workspace. Pass the same class to every
`add_typer` sub-app; a sub-app without it keeps Typer's own screen.

Commands are grouped by Typer's `rich_help_panel`, and a command with none lands
under `Commands`. Examples come from a command's `epilog`, one per line as
`command  # note`. The logo prints on the root page only, and only on a UTF-8
terminal with colour on and 256 colours or more. It is the roll with `SUSHI SYSTEMS`
beside it when the console is at least 72 columns wide (68 without the glow), the
roll alone when only that fits (20 columns with the glow, 16 without), and nothing
below that.

On a dark terminal the roll gets a white glow. `sushicore` decides that from
`COLORFGBG` and otherwise leaves the glow off, so a light terminal keeps its look.
Windows Terminal does not set the variable; say it once in the CLI's config:

```toml
[cli]
background = "dark"   # auto | dark | light
```

`SUSHI_CLI_BACKGROUND` sets the same thing from the environment.

If drawing the page fails, `--help` logs one warning under `sushicore.help` and shows
Typer's own screen.

Typer turns an app with one command and no callback into a plain command, so
the group never sees it and Typer's own screen stays.

## Tables

`console.table(columns, rows, title)` draws a header row, one rule under it and the rows, with no
frame. A cell whose whole text is a status word is coloured from the theme: `OK` in the success
style, `MISSING`, `FAIL` and `ERROR` in the error style, `WARN` in the warn style, and `NOT NEEDED`,
`SKIPPED` and `N/A` muted. A bracket in a cell is text unless it names a style, so
`pkg[extra]` prints whole while `[dim]x[/dim]` still dims.

`group_by="Owner"` names a column whose values become headings above their rows. That column
drops out of the table, the remaining columns line up across all groups, and the last column
wraps under itself. It only changes the terminal: `--json` still carries every column and row
in the same `table` event, and a renderer written before `group_by` existed keeps working for
every call that does not use it.

## Machine-readable output

`build_console(paths, machine=True)` selects `JsonRenderer`; `LazyConsole.machine = True`
does the same for a console built on first use, so a CLI sets it while parsing its
command line. Theme and icons are still loaded. The event vocabulary lives in
`sushicore.events`; `event_line(kind, **fields)` is its one serialisation.

One JSON object per line, UTF-8, no other bytes on stdout. Anything printed through
`console.console` (the raw Rich console) goes to stderr, so stdout stays parseable.
Keys are stable; the desktop application's schema depends on them.

```json
{"event": "line",     "level": "info",   "message": "..."}          level ∈ info|success|warn|error
{"event": "command",  "command": "cmake -S . -B build"}
{"event": "header",   "title": "SushiStack Install"}
{"event": "panel",    "title": "...", "body": "..."}
{"event": "table",    "title": "...", "columns": ["A","B"], "rows": [["a1","b1"]]}
{"event": "progress", "label": "install-deps", "index": 2, "count": 4, "fraction": 0.5}   fraction may be null
{"event": "result",   "ok": true, "payload": {}}
{"event": "prompt",   "id": "confirm-1", "message": "...", "default": "n"}               default may be null
```

A `prompt` event is answered by one line on stdin. The renderer reads it and returns it
stripped; an empty line returns the default; EOF returns the default. The `level` of a
`line` event is the first of `info`, `success`, `warn`, `error` named in the icon prefix,
case-insensitively; a prefix that names none of them (an emoji set, an empty prefix)
yields `info`.

The design is in `docs/agent/specs/2026-09-05-hub-design.md`, sections 4 and 7.

## Config schema

Add a `[cli]` table to your repo's existing `cli/config.toml` /
`cli/config.local.toml` (the same layered files each Sushi* CLI already
resolves for build config):

```toml
[cli]
theme = "default"   # preset name — see sushicore.theme.known_themes()
icons = "text"      # preset name — see sushicore.icons.known_icon_sets()
color = "auto"      # auto | always | never

[cli.colors]        # optional: partial override merged onto the preset
error = "bold red on white"

[cli.icon_overrides] # optional: partial override merged onto the icon preset
warn = "‼"

[cli.windows]       # optional: platform-specific override, same keys as above
icons = "minimal"
```

Precedence (low to high): built-in preset -> `config.toml` -> `config.local.toml`
-> `SUSHI_CLI_THEME` / `SUSHI_CLI_ICONS` / `SUSHI_CLI_COLOR` env vars ->
`NO_COLOR` (always forces `color = "never"` when set, per no-color.org).

To change your CLI's colors: edit `cli/config.local.toml` (gitignored,
machine-local) or export `SUSHI_CLI_THEME=mono` — no code change, no rebuild.

## Using it in a Sushi* CLI

```python
# sushiruntime/console.py (or sushiengine/, sushistack/)
from pathlib import Path
from sushicore import build_console
from .config import config_dir  # each repo's own config-dir discovery

_cfg_dir = config_dir()
console = build_console([_cfg_dir / "config.toml", _cfg_dir / "config.local.toml"])

info = console.info
success = console.success
warn = console.warn
error = console.error
command = console.command
header = console.header
fail_panel = console.fail_panel
table = console.table          # table(columns, rows, title="")
progress = console.progress    # progress(label, index, count, fraction=None)
result = console.result        # result(ok, payload=None)
prompt = console.prompt        # prompt(message, default=None) -> str
```

`build_console` only reads the `[cli]` table — it's safe to hand it the exact
same file list a repo already loads for its `[tool]` build config.

## Installing

sushicore is not published to any package index. It is a checkout that the other
CLIs inject, so it does not resolve as a normal pip dependency. You do not
install it directly in normal use:

- **End users** never handle it. The SushiStack bootstrap
  (`curl … | bash` / `irm … | iex`) clones it into `<workspace>/sushicore`, and
  `hub install-cli <module>` injects it (editable) into each module CLI's pipx
  venv automatically.
- **`hub status`** shows where the checkout is and its state (`fetched`,
  `linked`, `sibling`, or `missing`), so it is visible rather than a black box.

### Working on sushicore itself

Point the workspace at your own checkout so every CLI uses it:

```bash
hub link sushicore /path/to/sushicore    # records it in modules.local.toml
```

You can also override the lookup for one command with the `SUSHICORE_DIR`
environment variable. Resolution order is: `SUSHICORE_DIR` → an `hub link sushicore`
path → `<workspace>/sushicore` (the fetched checkout) → a sibling checkout next to
the workspace. Because injection is editable, edits to your checkout apply to the
installed `sr` / `se` / `hub` without reinstalling.

For a standalone editable install into the current environment:

```bash
pip install -e .
```