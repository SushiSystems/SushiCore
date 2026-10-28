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

Source: not compiled

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

Source: not compiled

Pass the same class to every `add_typer` sub-application. What the page shows and when the logo
appears is in [`sushicore/help/README.md`](../../source/sushicore/help/README.md).

## The shared surfaces

Every Sushi CLI registers the same surfaces, each with one call.

| Call | Gives the CLI |
| --- | --- |
| `sushicore.root_options.register_root_options(app, distribution=...)` | `--version` and `--describe`, the command catalogue as JSON |
| `sushicore.diag_commands.register_diagnostic_commands(app, diagnostics, program=..., panel=...)` | `config` and `env` |
| `sushicore.provision.commands.register_provision_commands(app, module)` | `setup`, `doctor`, `link`, `unlink` |
| `sushicore.provision.package_command.register_package_command(app, module)` | `package`, which installs a built tree to a prefix; every library CLI registers it |
| `sushicore.aliases.AliasTable(program, aliases)` | Old spellings that still run, hidden, and name their replacement |
| `sushicore.entry.run(app, report)` | An entry point that turns a `SushiCoreError` into one line and exit code 1 |

`register_root_options` installs the application's callback, so the application must not have
one of its own. A CLI that needs a root option of its own builds its callback from
`version_option` and `describe_option` in the same module.

`register_diagnostic_commands` takes `env=False` from a CLI whose `env` command has flags of its
own and is declared there.

`AliasTable` prints one notice per process, to a terminal only. Setting
`<PROGRAM>_NO_DEPRECATION_NOTICE=1` silences it, for example `SR_NO_DEPRECATION_NOTICE=1`.

`package` takes `--build-dir` (default `build`), `--prefix` (default `build/dist`), `--no-archive`
and `--force`. It runs `cmake --install` of the tree into the prefix and CPack unless
`--no-archive` is given. The install prints its command and one line counting the files it
copied and the ones already up to date; cmake's own lines appear only when the install fails.
It stops when the tree is not configured, and clears a prefix it did not stage only with
`--force`.

A CLI whose project links Sushi libraries consumes them as built packages. Before the configure
it calls `cfg.sushi_packages(root, build_type, options)`, which returns a `PackageSet`. The CLI
prints `package_set.lines()`, appends `cfg.sushi_definitions(root, package_set)` and
`package_set.definitions()` to the configure arguments, and prepends
`package_set.run_dirs(cfg.platform)` to `PATH` or `LD_LIBRARY_PATH` with
`build_env.prepend_path`. `sushi_packages.configure_arguments` builds that argument list, and
`sushi_packages.RunDirs(file_name)` keeps the run-time folders in the build tree, so `test` and `run`
prepend them without resolving again. `options` maps a library name to the extra `build` arguments that
library takes; `libraries=["sushilog"]` resolves only the named libraries and what they depend on, and
`sushi_definitions` then adds no `-D<NAME>_DIR` for a library left out; a flag such as `--distributed` is the consumer's to map. A CLI that is also a
library takes `--build-dir <path>` and `--lean` on `build`, which sushicore passes when it
builds the library's package, and honours `SUSHISTACK_CXX` over its configured compiler.

The provisioning commands and the `ModuleProvision` value they are registered from are in
[`sushicore/provision/README.md`](../../source/sushicore/provision/README.md).

## The entry point

The console script names a `main` function that hands the application to `entry.run`:

```python
from sushicore import entry

from . import console
from .cli import app


def main() -> None:
    entry.run(app, lambda message: console.error(message))
```

Source: not compiled

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
