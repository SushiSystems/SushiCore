# Frequently asked questions

Short answers for someone who uses or extends one of the Sushi command line tools and meets
SushiCore for the first time: what the package is, how to install it, how a CLI takes its
shared surfaces from it, and what is recorded as not working. Each answer links to the manual
page that holds the detail.

## What is SushiCore and who uses it?

SushiCore is the shared core of the Sushi developer CLIs. It is one Python package,
`sushicore`, and seven CLIs import it: `hub`, `sr`, `se`, `sa`, `sb`, `sd` and `st`. They use it
to locate a workspace, load layered TOML configuration, print to a terminal or to a JSON stream,
draw their help screens, drive cmake and ctest, and install and check what a repository needs to
build.

It is a library for those CLIs. It installs no console script, and it registers commands on
their Typer applications without having an application of its own. It knows nothing about SYCL,
a renderer, or any one module's schema. The [architecture overview](../architecture/OVERVIEW.md)
lists what each module of the package owns.

## How do I install SushiCore?

SushiCore is published on PyPI as `sushicore`.

```bash
pip install sushicore            # workspace, configuration, console, cmake driver
pip install "sushicore[typer]"   # the same, plus Typer
```

Typer is an optional extra. A CLI that uses `help_group`, the root options, the diagnostic
commands or the provisioning commands needs it; `import sushicore` alone does not. All seven
Sushi CLIs require `sushicore>=0.7.0`.

To work from a checkout, clone `https://github.com/SushiSystems/SushiCore` and run
`pip install -e ".[typer]"` in it. A CLI installed with pipx has its own environment, so the
checkout goes into that environment with
`pipx inject --editable <cli-package> /path/to/SushiCore`. [Installing](../getting_started/INSTALL.md)
also covers the tests and the checkers.

## Which Python versions and operating systems does it run on?

SushiCore needs Python 3.10 or later. CI runs the test suite on Ubuntu and Windows with Python
3.10 and 3.11. The checkers under `tools/` need Python 3.11.

A platform override table in a config file is named after `platform.system()` in lower case:
`windows`, `linux` or `darwin`. A dependency fragment pins download digests for two platforms,
`windows` and `linux`. See [Installing](../getting_started/INSTALL.md),
[Configuration](../reference/CONFIGURATION.md) and
[Dependency fragment](../reference/DEPENDENCY_FRAGMENT.md).

## How does a CLI adopt SushiCore?

The CLI is a Typer application and installs SushiCore with the `typer` extra. It builds its
console through `LazyConsole` on first use, not at import, so that `--help` runs outside a
checkout. It passes `help_group` as the class of its Typer application and of every `add_typer`
sub-application. Its console script names a `main` function that hands the application to
`sushicore.entry.run`, which turns a `SushiCoreError` into one line and exit code 1.

Every Sushi CLI then registers the same surfaces, each with one call:

- `register_root_options` gives `--version` and `--describe`, the command catalogue as JSON.
- `register_diagnostic_commands` gives `config` and `env`.
- `register_provision_commands` gives `setup`, `doctor`, `link` and `unlink`.
- `AliasTable` keeps old command spellings running, hidden, and names their replacement.

`build`, `test`, `run` and `clean` stay in each CLI. [CLI integration](CLI_INTEGRATION.md) has
the code for each step.

## How does configuration work, and which source wins?

A CLI hands SushiCore its config files, by convention `cli/config.toml` and
`cli/config.local.toml` in the repository the CLI builds. The second is machine-local and not
committed. Appearance comes from the `[cli]` table only: `theme`, `icons`, `color` and
`background`. From lowest to highest precedence:

1. The built-in preset.
2. Each config file in the order given, so `config.local.toml` wins over `config.toml`.
3. `SUSHI_CLI_THEME`, `SUSHI_CLI_ICONS`, `SUSHI_CLI_COLOR` and `SUSHI_CLI_BACKGROUND`.
4. `NO_COLOR`, which forces `color = "never"` whenever it is set.

The same files can hold the `[tool]` build configuration. A `[tool]` table is merged with its
`[tool.<platform>]` override, and a `<PREFIX>_<TOOL>` environment variable such as `SR_CMAKE`
then overrides one tool path of one CLI. [Configuration](../reference/CONFIGURATION.md) lists
every key and variable, and what a bad value does.

## What is the dependency root?

The dependency root is the one folder per machine that holds installed toolchains and tools. It
is the folder `SUSHISYSTEMS_HOME` names, and `~/.sushisystems` when that variable is unset.
`registry.toml` in it records what is installed and which modules use it.

New installs go to the dependency root. Toolchains and vcpkg are looked up there first, then in
the folder `SUSHISTACK_DEPS_DIR` names and in a legacy `<workspace>/dependencies` tree; a legacy
tree is read and never written. [`sushicore/provision/README.md`](../../sushicore/provision/README.md)
describes the root and how it is moved to another directory.

## What do `setup` and `doctor` do?

`setup` installs what a module needs to build and then runs `doctor`. It reads the module's
dependency fragment, `cli/sushistack.deps.toml` by default, and through `[module] depends_on`
the fragment of every module it builds on. It never clones. `--dry-run` shows the run and
changes nothing, `--toolchain NAME` also installs that toolchain, and `--no-gpu` skips the GPU
toolkit.

`doctor` is a read-only report. It checks the build tools, the checkouts of the modules this
one builds on, the toolchain capabilities, the fragments, the toolchain stamps and the download
digests, then the module's own checks. `--for GROUP` restricts the report to one group: `build`,
`test`, `infer` or `eval`. It exits with code 1 when a required check fails.

No module needs `hub` installed to use either command. The options and exit codes are in
[`sushicore/provision/README.md`](../../sushicore/provision/README.md).

## What do `link` and `unlink` do?

`link` records a module in a workspace's `[modules]` table and writes a `[link] workspace`
pointer into the module's `cli/config.local.toml`. `unlink` removes both. A workspace is a
folder holding `.sushistack/workspace.toml`, which records the modules linked to it and the
tools they share.

Linking copies nothing. Config loading follows the pointer and layers the linked workspace's
`[tool]` table at read time. `SUSHISTACK_HOME` wins over the pointer, and a pointer to a deleted
workspace is ignored. The workspace `link` uses is `--workspace PATH`, else `SUSHISTACK_HOME`,
else the first folder above the project root that holds `.sushistack`. See
[`sushicore/provision/README.md`](../../sushicore/provision/README.md).

## What is the JSON event stream?

In machine mode a console writes one JSON object per line to stdout, in UTF-8, for a program to
read. The SushiHub desktop application is the reader it was designed for. The event kinds are
`line`, `command`, `header`, `panel`, `table`, `progress`, `result` and `prompt`, and `event` is
always the first key:

```json
{"event": "line", "level": "info", "message": "..."}
{"event": "result", "ok": true, "payload": {}}
```

A CLI turns the stream on with `build_console(paths, machine=True)`, or by setting
`LazyConsole.machine = True` while it parses its command line. Of the seven CLIs only `hub`
offers the stream, as `--json`. A `prompt` event is answered by one line on stdin.
[JSON events](../reference/JSON_EVENTS.md) gives the fields of every event.

## How is SushiCore licensed?

SushiCore is source-available. It is free for non-commercial use under the PolyForm
Noncommercial License 1.0.0, and [`LICENSE`](../../LICENSE) is the binding text. The permitted
purposes it lists are personal, non-commercial use and use by the non-commercial organisations
it names.

Any commercial purpose needs a separate, paid licence from Sushi Systems. That includes use
inside a company, use in paid client work, and use in a product or service that is sold.
[`COMMERCIAL.md`](../../COMMERCIAL.md) says how to ask for one: write to `hello@sushisystems.io`
with what you want to build and who will use it.

Versions 0.1.0 to 0.4.0 were published under the Apache License 2.0 and stay available under
it; 0.7.0 is the first version under the licence above. The [README](../../README.md) gives the
commit boundary, and `NOTICE.md` lists the third-party software.

## What is known not to work?

[Known issues](../reference/KNOWN_ISSUES.md) records the open defects. Those a user of a CLI
meets first:

- With the `emoji`, `minimal` or `none` icon set, every warning and error in the JSON stream is
  reported with `level` `info`.
- A child process inherits stdout, so in machine mode stdout carries more than events.
- `setup`, `link` and `unlink` end without a `result` event, and `config` and `env` emit no
  `table` or `prompt` event.
- No fragment entry pins a `sha256` yet, so every download is extracted or run unverified, with
  a warning. Downloads inside a shell pipeline and git clones are not verified at all.
- The CUDA installer runs silently, the oneAPI installer runs with `--eula accept`, and winget
  runs with `--accept-package-agreements`, each on the user's behalf.
- `link --workspace PATH` does not check the path for the workspace marker and creates
  `.sushistack/workspace.toml` there.

The limits of the help screen are in [`sushicore/help/README.md`](../../sushicore/help/README.md).

## Does SushiCore accept outside contributions?

Contributions from outside Sushi Systems are not accepted yet. The [README](../../README.md)
states this beside the licence.
