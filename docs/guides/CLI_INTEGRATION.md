# CLI integration

How a Sushi CLI takes its console, its help screen and its shared commands from SushiCore. The
CLI is a Typer application; install SushiCore with the `typer` extra.

## The console

Build the console on first use, not at import. Finding the CLI's `cli/` directory walks up for a
root marker and fails outside a checkout, so a console built at import breaks `--help` there.
`LazyConsole` takes the resolver and calls it the first time something prints:

```python
# <package>/console.py
from sushicore.cli_console import LazyConsole

from .config import config_dir  # the CLI's own resolver for its cli/ directory

lazy = LazyConsole(config_dir)


def __getattr__(name: str):
    return lazy.attribute(name)
```

Other modules of the CLI then write `from . import console` and call `console.info(...)`,
`console.error(...)`, `console.table(...)` and the rest of the facade. `lazy.get()` returns the
`Console` object itself. Outside a checkout the console is built with no config files and uses
the defaults.

`LazyConsole` hands the console the files `config.toml` and `config.local.toml` from that
directory. `build_console` reads only their `[cli]` table, so the same files can hold the
`[tool]` build configuration. [Configuration](../reference/CONFIGURATION.md) lists the keys.

Set `lazy.machine = True` while parsing the command line to get the JSON event stream; see
[JSON events](../reference/JSON_EVENTS.md).

## The help screen

```python
import typer
from sushicore.typer_help import help_group

from . import console

app = typer.Typer(cls=help_group(console.lazy.get), rich_markup_mode="rich")
```

Pass the same class to every `add_typer` sub-application. What the page shows and when the logo
appears is in [`sushicore/help/README.md`](../../sushicore/help/README.md).

## The shared surfaces

Every Sushi CLI registers the same surfaces, each with one call.

| Call | Gives the CLI |
| --- | --- |
| `sushicore.root_options.register_root_options(app, distribution=...)` | `--version` and `--describe`, the command catalogue as JSON |
| `sushicore.diag_commands.register_diagnostic_commands(app, diagnostics, program=..., panel=...)` | `config` and `env` |
| `sushicore.provision.commands.register_provision_commands(app, module)` | `setup`, `doctor`, `link`, `unlink` |
| `sushicore.aliases.AliasTable(program, aliases)` | Old spellings that still run, hidden, and name their replacement |
| `sushicore.entry.run(app, report)` | An entry point that turns a `SushiCoreError` into one line and exit code 1 |

`register_root_options` installs the application's callback, so the application must not have
one of its own. A CLI that needs a root option of its own builds its callback from
`version_option` and `describe_option` in the same module.

`register_diagnostic_commands` takes `env=False` from a CLI whose `env` command has flags of its
own and is declared there.

`AliasTable` prints one notice per process, to a terminal only. Setting
`<PROGRAM>_NO_DEPRECATION_NOTICE=1` silences it, for example `SR_NO_DEPRECATION_NOTICE=1`.

The provisioning commands and the `ModuleProvision` value they are registered from are in
[`sushicore/provision/README.md`](../../sushicore/provision/README.md).

## The entry point

The console script names a `main` function that hands the application to `entry.run`:

```python
from sushicore import entry

from . import console
from .cli import app


def main() -> None:
    entry.run(app, lambda message: console.error(message))
```

The reporter looks the printer up when it is called. Passing `console.error` directly reads the
attribute before `run` starts, and a console built from a malformed config file fails on that
read. When the reporter itself raises a `SushiCoreError`, `run` prints the line to stderr.

A failure the user can act on derives from `sushicore.errors.SushiCoreError`. Anything else
stays a traceback.

## Building and running

`build`, `test`, `run` and `clean` stay in each CLI. SushiCore supplies what they call:
`proc.Runner` to spawn a child, `cmake_driver.CMakeDriver` for the cmake and ctest command
lines, `build_env` for the environment they run under and `discovery.ExecutableIndex` to list
what a build produced.
