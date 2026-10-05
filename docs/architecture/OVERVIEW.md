# Architecture overview

SushiCore is one Python package, `sushicore`, with three sub-packages. Seven CLIs import it:
`hub`, `sr`, `se`, `sa`, `sb`, `sd` and `st`. It registers commands on their Typer applications
and has no application of its own.

## The modules

### Locating a project and loading its configuration

| Module | Owns |
| --- | --- |
| `workspace` | The walk up to a marker file, the `[tool]` table merged with its platform override, the workspace's `[modules]` table and a module's `[link]` pointer |
| `config_base` | `ToolConfig`, the tool-path fields every CLI shares, and the layered load and `[tool]` write around them |
| `module_config` | `ModuleConfig`: a module's project root and its layered config, the linked workspace's `[tool]` table included |
| `stack_config` | `StackConfig`: the compiler and vcpkg of a module that consumes a dependency root, and `locate_sibling` |
| `profile` | `ModuleProfile`: what one CLI says about itself, such as its name, command, environment prefix and root marker |
| `deps_fragment` | The one reader of a `sushistack.deps.toml` fragment |
| `errors` | `SushiCoreError` and `ConfigError`, the failures an entry point prints as one line |

### Printing

| Module | Owns |
| --- | --- |
| `config` | `load_appearance`: the `[cli]` table and the `SUSHI_CLI_*` variables resolved into one `AppearanceSpec` |
| `theme` | `Theme`, the style tokens, and the presets `default`, `mono` and `muted` |
| `icons` | `IconSet`, the prefix printed before a line, and the presets `text`, `emoji`, `minimal` and `none` |
| `renderer` | The `Renderer` protocol and its three backends: `RichRenderer`, `PlainRenderer`, `JsonRenderer` |
| `events` | The event kinds `JsonRenderer` writes and `event_line`, their one serialisation |
| `console` | `Console`, the facade a CLI calls: `info`, `success`, `warn`, `error`, `command`, `header`, `fail_panel`, `table`, `progress`, `result`, `prompt` |
| `cli_console` | `LazyConsole`, which builds the console on first use so `--help` runs outside a checkout |
| `markup` | `escape_unknown_tags`, which keeps a bracket as text unless it names a style |
| `terminal_background` | `is_dark_background`, decided from the `background` setting and `COLORFGBG` |
| `windows_console` | `enable_virtual_terminal` for a classic Windows console |
| `brand` | The Sushi Systems mark and wordmark as palettes and pixel grids |
| [`ui`](../../sushicore/ui/README.md) | One file per terminal element, each drawn from a `Theme` |
| [`help`](../../sushicore/help/README.md) | A help screen as data and the page that lays it out |
| `typer_help` | `help_group`, which wires the help page into a Typer application |
| `typer_theme` | `apply_typer_theme`, which recolours Typer's own help screen |

`build_console` in `sushicore/__init__.py` wires the printing modules together from the config
files a CLI hands it.

### Building

| Module | Owns |
| --- | --- |
| `proc` | `Runner`, which spawns a child process for a CLI |
| `build_env` | The environment a build runs under, with the vcvars snapshot on Windows |
| `cmake_cache` | What a `CMakeCache.txt` says about how its tree was configured |
| `cmake_driver` | `CMakeDriver`, the cmake and ctest command lines |
| `toolchain_args` | The compiler and vcpkg prefix arguments of a configure |
| `discovery` | `ExecutableIndex`, the built executables under a build tree |

### The surfaces every CLI registers

| Module | Owns |
| --- | --- |
| `root_options` | `--version` and `--describe` |
| `describe` | The command catalogue `--describe` prints as JSON |
| `diag`, `diag_commands` | `Diagnostics` and the `config` and `env` commands registered from it |
| `aliases` | `AliasTable`: old spellings that still run, hidden, and name their replacement |
| `entry` | `run`, the entry point that turns a `SushiCoreError` into one line and exit code 1 |
| [`provision`](../../sushicore/provision/README.md) | The dependency root, the registry, the doctor and the commands `setup`, `doctor`, `link`, `unlink` |

## Rules the code keeps

- `Console` talks to the `Renderer` protocol and never to Rich. A renderer is any object with
  the protocol's eight methods (`line`, `command`, `header`, `panel`, `table`, `progress`,
  `result`, `prompt`) and its `raw` property.
- `Theme` and `IconSet` are data. A new preset is registered with `register_theme` or
  `register_icon_set`; no other module changes.
- A component in `ui` reads `Theme` and `brand` and nothing else. `tests/test_ui_architecture.py`
  fails when one imports more.
- `typer_help` is the only module that imports Typer when it is loaded. `typer_theme`,
  `root_options`, `diag_commands` and `provision/commands.py` import it inside the function that
  needs it, and `aliases`, `describe` and `entry` only for type checking, so `import sushicore`
  works without the `typer` extra.
- Inside `provision`, lower layers do not import higher ones; the layer table is in
  [`docs/design/PROVISION.md`](../design/PROVISION.md).

The import cycles that break these rules today are listed in
[Known issues](../reference/KNOWN_ISSUES.md).
