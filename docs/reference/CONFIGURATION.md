# Configuration

What SushiCore reads from a CLI's config files and from the environment.

## The `[cli]` table

A CLI hands `build_console` its config files, low to high precedence. By convention they are
`cli/config.toml` and `cli/config.local.toml` in the repository the CLI builds; the second is
machine-local and not committed. Only the `[cli]` table is read for appearance.

```toml
[cli]
theme = "default"      # default | mono | muted, or a name given to register_theme
icons = "text"         # text | emoji | minimal | none, or a name given to register_icon_set
color = "auto"         # auto | always | never
background = "auto"    # auto | dark | light

[cli.colors]           # optional, merged onto the theme preset
error = "bold red on white"

[cli.icon_overrides]   # optional, merged onto the icon preset
warn = "!!"

[cli.windows]          # optional, same keys, wins on that platform
icons = "minimal"
```

The platform table is named after `platform.system()` in lower case: `windows`, `linux` or
`darwin`.

| Key | Effect |
| --- | --- |
| `theme` | The style tokens: `info`, `success`, `warn`, `error`, `cmd`, `header`, `panel_border`, `muted` |
| `icons` | The prefix before a line, such as `[INFO]` in the `text` set |
| `color` | `auto` colours a TTY and nothing else |
| `background` | Whether the logo gets its white glow; `auto` reads `COLORFGBG` and otherwise leaves the glow off |

## Precedence

Low to high:

1. The built-in preset.
2. Each config file in the order given, so `config.local.toml` wins over `config.toml`.
3. `SUSHI_CLI_THEME`, `SUSHI_CLI_ICONS`, `SUSHI_CLI_COLOR`, `SUSHI_CLI_BACKGROUND`.
4. `NO_COLOR`, which forces `color = "never"` whenever it is set.

## Bad values

| Value | Result |
| --- | --- |
| A config file that is not valid TOML | `ConfigError`, which the entry point prints as one line with exit code 1 |
| An unknown `theme` or `icons` name | `ConfigError`, the same way |
| An unknown `color` | Falls back to `auto` without a message |
| An unknown `background` | Falls back to `auto` without a message |

## Environment variables

| Variable | Read by | Meaning |
| --- | --- | --- |
| `SUSHI_CLI_THEME`, `SUSHI_CLI_ICONS`, `SUSHI_CLI_COLOR`, `SUSHI_CLI_BACKGROUND` | `config.py` | Override the `[cli]` key of the same name |
| `NO_COLOR` | `config.py` | Turns colour off |
| `COLORFGBG` | `terminal_background.py` | Tells a dark terminal from a light one when `background` is `auto` |
| `SUSHISTACK_HOME` | `module_config.py`, `stack_config.py`, `provision/` | Names the workspace; wins over a module's `[link]` pointer |
| `SUSHISYSTEMS_HOME` | `provision/home.py` | Names the dependency root; the default is `~/.sushisystems` |
| `SUSHISTACK_DEPS_DIR` | `provision/home.py`, `stack_config.py` | Names a legacy dependency tree to read |
| `<PREFIX>_<TOOL>` | `profile.py` | Overrides one tool path of one CLI, such as `SR_CMAKE`; the prefix is `ModuleProfile.env_prefix` |
| `<PROGRAM>_NO_DEPRECATION_NOTICE` | `aliases.py` | Set to `1`, silences the notice an old command spelling prints |
| `CUDA_PATH`, `ROCM_PATH` | `provision/gpu/` | Where the CUDA and ROCm locators look first |
