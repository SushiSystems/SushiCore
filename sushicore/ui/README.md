# sushicore.ui

One file per terminal element. `RichRenderer.table`, `panel` and `header` draw through these
components, and the help page is laid out from them.

## What it owns

| Component | File | Draws |
| --- | --- | --- |
| `Logo` | `logo.py` | The Sushi Systems mark in half-block characters, with the wordmark beside it and a white glow behind it when asked |
| `Header` | `header.py` | A section header |
| `Panel` | `panel.py` | A bordered block of text under a title |
| `Table` | `table.py` | A header row, one rule under it and the rows, with no frame |
| `Title` | `title.py` | The one-line title of a help page |
| `Usage` | `usage.py` | The usage line of a command |
| `DefinitionList` | `definition_list.py` | Terms with their descriptions, as the help page lists commands and options |

`component.py` holds `Component`, the protocol all of them satisfy: `render(theme)` returns a
Rich renderable. Each component is a frozen dataclass.

## What it depends on

`sushicore.theme` for the styles, `sushicore.brand` for the logo's palette and pixel grid,
`sushicore.markup` for bracket handling, and Rich. A component reads no console, no config and
no environment. `tests/test_ui_architecture.py` fails when a file here imports more or holds
more than one component.

## Tables

`console.table(columns, rows, title)` reaches `Table`. A cell whose whole text is a status word
is coloured from the theme; `K_STATUS_STYLES` in `table.py` is the list.

| Style | Words |
| --- | --- |
| success | `OK` |
| error | `MISSING`, `FAIL`, `FAILED`, `ERROR` |
| warn | `WARN`, `WARNING` |
| muted | `NOT NEEDED`, `SKIPPED`, `N/A` |

A bracket in a cell is text unless it names a style, so `pkg[extra]` prints whole while
`[dim]x[/dim]` still dims.

`group_by="Owner"` names a column whose values become headings above their rows. That column
drops out of the table, the remaining columns line up across all groups, and the last column
wraps under itself. Grouping changes only the terminal: the JSON `table` event still carries
every column and row.

## The logo

`Logo(wordmark=True, glow=False)` has a `width` in columns, measured from the grid it draws:

| Logo | Width |
| --- | --- |
| Mark and wordmark, with the glow | 72 |
| Mark and wordmark | 68 |
| Mark alone, with the glow | 20 |
| Mark alone | 16 |

`sushicore.help.choose_logo` picks among them for a console.
