# sushicore

Shared, config-driven CLI presentation layer for the Sushi* developer CLIs
(`sr` / sushiruntime, `se` / sushiengine, `ss` / sushistack). One seam for
colors, icons, and output formatting so a visual change (e.g. "I want
different CLI colors") is a config edit in one place, not a hunt through
three hardcoded `console.py` files.

## Design

Small, swappable pieces (SOLID), not one monolith:

- `Theme` (`sushicore.theme`) — pure data: style tokens (`info`, `success`,
  `warn`, `error`, `cmd`, `header`, `panel_border`). Presets: `default`,
  `mono`, `muted`. Register your own with `register_theme(name, Theme(...))`.
- `IconSet` (`sushicore.icons`) — pure data: the prefix/glyph printed before a
  line. Presets: `text` (`[INFO]`, ...), `emoji`, `minimal`, `none`.
  Register your own with `register_icon_set(...)`.
- `Renderer` (`sushicore.renderer`) — a `Protocol` describing how a themed
  message actually gets drawn. `RichRenderer` is the default (colored, via
  Rich); `PlainRenderer` is the no-color fallback used for `NO_COLOR`,
  `color = "never"`, or a non-TTY stream. Any object implementing the same
  four methods is a drop-in replacement — e.g. a future JSON renderer for
  machine-readable CI logs.
- `Console` (`sushicore.console`) — the facade every CLI actually calls
  (`console.info(...)`, `console.error(...)`, ...). It only translates
  semantic calls into renderer calls using a theme + icon set; it never picks
  a color itself.
- `build_console()` (`sushicore.__init__`) — the factory that wires the above
  together from layered config. This is the one function a CLI needs to call.

Themes and icon sets are pure data, so most customization needs **no code at
all** — just a config file.

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
```

`build_console` only reads the `[cli]` table — it's safe to hand it the exact
same file list a repo already loads for its `[tool]` build config.

## Installing

sushicore is not published to any package index. It is a checkout that the other
CLIs inject, so it does not resolve as a normal pip dependency. You do not
install it directly in normal use:

- **End users** never handle it. The SushiStack bootstrap
  (`curl … | bash` / `irm … | iex`) clones it into `<workspace>/sushicore`, and
  `ss install-cli <module>` injects it (editable) into each module CLI's pipx
  venv automatically.
- **`ss status`** shows where the checkout is and its state (`fetched`,
  `linked`, `sibling`, or `missing`), so it is visible rather than a black box.

### Working on sushicore itself

Point the workspace at your own checkout so every CLI uses it:

```bash
ss link sushicore /path/to/sushicore    # records it in modules.local.toml
```

You can also override the lookup for one command with the `SUSHICORE_DIR`
environment variable. Resolution order is: `SUSHICORE_DIR` → an `ss link sushicore`
path → `<workspace>/sushicore` (the fetched checkout) → a sibling checkout next to
the workspace. Because injection is editable, edits to your checkout apply to the
installed `sr` / `se` / `ss` without reinstalling.

For a standalone editable install into the current environment:

```bash
pip install -e .
```