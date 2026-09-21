# Terminal components: a logo, quiet tables and a themed help screen

**Status:** Approved. Implementation plan: `docs/agent/plans/2026-09-21-terminal-components.md`.

sushicore draws every terminal element inside `RichRenderer`, and `--help` is Typer's own screen
with recoloured constants. This spec moves each element into its own component, the way
`sushiweb/packages/brand` keeps one file per element (`Logo`, `Card`, `Notice`, `PageHeader`),
and builds the new logo, the quiet table and the help screen from those components.

## Decisions already taken

| Question | Decision |
| --- | --- |
| Where the logo prints | Root help and a bare invocation. Sub-command help gets a one-line title instead. Command output never carries it. |
| Logo form | Half-block art (`▀▄█`): the roll in the four brand colours, `SUSHI` over `SYSTEMS` beside it in a hand-drawn 7-pixel font, and on a dark terminal a two-ring white glow behind the roll. |
| How help is drawn | sushicore draws it. Typer supplies the command tree and nothing else. |
| Help content | Command groups, examples, sub-command help in the same layout. |
| Component boundary | `Renderer` calls components. Its Protocol, `PlainRenderer` and `JsonRenderer` do not change. |

## Component layer

`sushicore/ui/` holds one file per component. A component is a frozen dataclass of props with
one method, `render(theme: Theme) -> RenderableType`, declared once in `ui/component.py` as the
`Component` Protocol. Siblings have the same shape, so adding the tenth component adds a file
and one line to `ui/__init__.py`, and edits none of the nine.

| File | Component | Draws |
| --- | --- | --- |
| `logo.py` | `Logo` | The roll, the wordmark and the glow from `brand.py`, two pixel rows per terminal row. |
| `header.py` | `Header` | A blank line and a titled rule. Look unchanged. |
| `panel.py` | `Panel` | A bordered body under a title. Look unchanged. |
| `table.py` | `Table` | Header row, one rule beneath it, no outer frame. |
| `title.py` | `Title` | A command name and its description. |
| `usage.py` | `Usage` | The `Usage:` line. |
| `definition_list.py` | `DefinitionList` | A heading over an aligned term column and text column. Commands, arguments, options and examples are each one of these. |

A component reads styles from `Theme` and colours from `brand.py`, and nothing else. Three
changes to those sources:

- `Theme` gains `muted` (default `dim`), used for table rules and secondary text. It is a new
  field with a default, so a downstream theme that does not set it keeps working.
- `Console` gains a read-only `theme` property, so `typer_help` can hand the theme to a page.
- `brand.py` holds the four logo colours (nori, rice, amber `#f0a500`, green) and the logo pixel
  grid as strings of palette keys. Only `Logo` reads it. The grid is traced once from
  `sushiweb/apps/web/public/images/logo-icon.png`, corrected by hand, and committed as data. The
  tracing script is not kept.

The `Table` look is one place: `rich.box.SIMPLE_HEAD`, no edge, the header in `theme.header`,
the rule in `theme.muted`. `RichRenderer.table`, `panel` and `header` build the matching
component and print it. Their signatures stay as they are.

## The logo

`Logo(indent=2, wordmark=True, glow=False)` draws from `brand.py`. The mark is an 18 by 16 pixel grid,
the roll plus two glow rings. The wordmark is a 50 by 16 pixel grid: `SUSHI` over `SYSTEMS`, drawn
by hand at 7 pixels tall with 2-pixel vertical strokes, because resampling the site's wordmark to
this height is unreadable. `SUSHI` is drawn in the terminal's own foreground colour, so it reads on
a dark and on a light terminal, and `SYSTEMS` is amber. The glow is two rings, `#8c8c8c` then
`#3d3d3d`, and it only draws when `glow` is true. Pixels that draw nothing are trimmed from the
mark's edges, so a logo without the glow has no empty margin. `Logo.width` is the columns one row
takes: 72 with the wordmark and glow, 68 with the wordmark alone, 20 and 16 for the mark alone.

Three things decide which logo, if any, a help page shows, and none of them is `Logo`'s business.
`typer_help` shows no logo unless the Rich console is a terminal, `no_color` is false, the colour
system is 256 colours or better and the encoding is UTF-8. `choose_logo(width, dark_background)`
then returns the lockup when it fits, the mark alone when only that fits, and nothing when neither
does. `dark_background` comes from `Console.dark_background`: `is_dark_background` reads the
`[cli] background` setting (`auto`, `dark` or `light`, also `SUSHI_CLI_BACKGROUND`) and, for `auto`,
the `COLORFGBG` variable. An unreadable value is treated as not dark, so a light terminal never gets
the glow. A terminal that sets no `COLORFGBG`, Windows Terminal among them, needs
`background = "dark"` once.

## Help

`sushicore/help/` is independent of Typer and Click's rendering.

- `model.py` defines `HelpModel`, pure data: name, description, usage, whether this is the root,
  sections of commands (`HelpSection`), arguments, options and examples.
- `from_click.py` builds a `HelpModel` from a Click command by duck typing, without importing
  Click. Groups come from Typer's `rich_help_panel` attribute, in the order the command lists
  its sub-commands (registration order for Typer, alphabetical for plain Click), a panel
  taking the place of its first command, with `Commands` for any command that names none.
  Typer stores a placeholder object there when a command names no panel, so only a string
  counts. Examples come from `epilog`: one command per non-empty line, an optional note after
  ` # `. The model's text is Rich markup. The reader escapes description, sub-command and
  parameter text unless the command's `rich_markup_mode` is `rich`, so a bracket in plain
  Click help prints as written and a stray `[/]` cannot raise.
- `page.py` defines `HelpPage`, which lays the model out: the `logo` it is given, on a root page only,
  `Title`, `Usage`, one `DefinitionList` per command group, then arguments, options and
  examples, each omitted when empty. A page knows the order and nothing about how a component
  draws.

`sushicore/typer_help.py` is the only module that imports Typer. `help_group(console)` takes
a callable returning the CLI's `Console` and returns a `TyperGroup` subclass. Its `format_help`
builds the model and the page and writes the page, drawn to the console's width and colour
setting, into Click's formatter. Writing through the formatter keeps `ctx.get_help()` working,
which `hub`'s bare invocation uses. Each CLI writes `typer.Typer(cls=help_group(...))` on the
root and on every `add_typer` sub-app, and supplies a provider for its `Console`, so `--help`
still runs outside a workspace.

Typer ignores a group's `command_class` (it builds each command with `command_info.cls or
TyperCommand`), so the group wraps `get_command` and replaces each child's `format_help` as it
hands the child out, unless the child is itself a help group. Measured on Typer 0.20 and Click
8.2.1: this renders `--help` correctly at the root, at a sub-group and at a leaf.

The existing `apply_typer_theme` stays until every CLI has moved. It becomes dead code for a CLI
that has, and its removal is a later, separate change.

## Machine output

Nothing here reaches `--json`. `JsonRenderer` still emits events. Help text goes through
Click's formatter to stdout, as it does today, and contains no event.

## Package layout

```
sushicore/
  brand.py
  terminal_background.py
  theme.py                  gains Theme.muted
  renderer.py               table, panel, header delegate to ui/
  typer_help.py
  ui/    __init__.py component.py logo.py header.py panel.py table.py
         title.py usage.py definition_list.py
  help/  __init__.py model.py from_click.py page.py logo_choice.py
```

Dependency direction is `typer_help` to `help` to `ui` to `theme` and `brand`, and `renderer` to
`ui`. Nothing points back up.

## Tests

- One test file per component in `tests/ui/`, rendering at a fixed width with a recording,
  colourless Rich console and asserting the text.
- `Logo`: a golden file of the truecolour output, plus a check that the grid is rectangular and
  uses only palette keys.
- `tests/test_ui_architecture.py`, the counterpart of `architecture.test.ts` in `packages/brand`.
  Every `ui/` file exports exactly one component whose name is the file's name in Pascal case,
  that component is a frozen dataclass with `render`, and the file imports only the standard
  library, `rich`, `..theme`, `..brand` and `.component`. No `ui/` file imports `help`.
- `tests/help/test_from_click.py` on a small Click tree: grouping, panel order, epilog examples,
  the default group.
- `tests/test_typer_help.py` through Typer's `CliRunner`: root and leaf output, the logo present
  on a colour terminal and absent when piped.
- `tests/test_console_semantics.py` keeps passing unchanged, which shows the `Renderer` contract
  did not move. `RichRenderer.table` gets a colourless test for the new look.

## Documentation and release

- `README.md` and `docs/README.md` gain a `sushicore.ui` and a `sushicore.help` row.
- `docs/reference/CHANGELOG.md` gets one line per change.
- Version 0.3.0 becomes 0.4.0. Everything added is new surface. The one visible change to an
  existing path is the table look, which no CLI parses.
- Typer becomes an optional extra, `typer = ["typer>=0.12"]`, and joins the `test` extra.
  sushicore already imports it in `typer_theme.py` behind an `ImportError` guard, so this
  records an existing dependency and adds none to a plain install.

## Adoption in `hub`

Second stage, after sushicore 0.4.0 is on PyPI. `sushihub/cli/sushistack/cli.py` passes
`cls=help_group(...)` to `app` and to `gui_app`, assigns each command a `rich_help_panel` and
writes its examples in `epilog`. The groups:

| Group | Commands |
| --- | --- |
| Workspace | `init`, `home`, `status` |
| Modules | `add`, `link`, `install-cli`, `update`, `sync` |
| Dependencies | `install`, `doctor`, `remove` |
| Account | `login`, `logout`, `whoami`, `license` |
| Desktop app | `gui` |

The screen lists groups in the order each first appears among the commands. Typer lists
registered commands before sub-apps, so `gui` comes last and the screen reads Workspace,
Modules, Dependencies, Account, Desktop app.

`hub`'s `pyproject.toml` raises its sushicore lower bound to 0.4.0, and `sushihub/cli/README.md`
and `docs/reference/CHANGELOG.md` change in the same commit. `hub --describe` and the JSON
contract are untouched.

## Known limit

A Typer app built with `rich_markup_mode=None` or `"markdown"` prints a backslash before the
bracketed extras Typer adds to a parameter (`\[default: a]`, `\[required]`). Typer escapes its
own extras whatever the mode, and the reader escapes them again. `"rich"` and Typer's default
mode are correct. `hub` sets `"rich"`; the other CLIs were not checked.

Typer under `rich_markup_mode="rich"` raises `MarkupError` on a stray `[/]` in a command's help,
and it does so for the whole root screen when only a child carries it. That is Typer 0.20's own
failure, reproduced without sushicore. `help_group` catches the page's error, logs one warning and
hands over to Typer, which then raises the same error, so `--help` still fails for that input.

## Not in this spec

- `sr`, `se`, `sa`, `sb`, `sd` and `st` adopt `help_group` on their own schedule.
- A `[cli]` setting to turn the logo off. `NO_COLOR` and a pipe already do.
- The documentation skeleton for sushicore (`docs/design/`, `docs/agent/plans/`, `docs/guides/`
  and the rest). It is a separate task; this spec is filed under `docs/agent/specs/`, which the
  repository did not have.

## Open items

- The logo grid size, roughly 22 by 20 pixels, is a starting point. It is fixed when the trace
  is checked in a real terminal.
