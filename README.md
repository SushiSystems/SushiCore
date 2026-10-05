# SushiCore

The shared core of the Sushi developer CLIs. `hub`, `sr`, `se`, `sa`, `sb`, `sd` and `st` all
import it for the same five things: locating a workspace, loading layered TOML configuration,
printing to a terminal or to a JSON stream, driving cmake and ctest, and reading the
`sushistack.deps.toml` fragment a repository writes about what it needs.

```bash
pip install sushicore
```

It is a library for those CLIs rather than a tool of its own: it installs no console script and
it knows nothing about SYCL, a renderer, or any one module's schema.

| Module | What it does |
|---|---|
| `sushicore.workspace` | Walks up for a marker, merges a `[tool]` table with its platform override |
| `sushicore.config_base` | The layered load: defaults, file, local file, environment |
| `sushicore.console`, `renderer`, `events`, `theme`, `icons` | One seam for human output and for `--json` |
| `sushicore.ui`, `sushicore.brand` | One file per terminal element (logo, header, panel, table, title, usage, definition list); each draws itself from a `Theme`, the logo from `brand` |
| `sushicore.help`, `sushicore.typer_help` | A themed help screen for a Typer CLI: `typer.Typer(cls=help_group(provider))` |
| `sushicore.cmake_driver`, `cmake_cache`, `proc`, `toolchain_args` | The configure, build and test driver the CLIs share |

## What a CLI takes from here

Every Sushi CLI registers the same surfaces from this package, so none can be the one without
them.

| Call | Gives the CLI |
| --- | --- |
| `sushicore.root_options.register_root_options(app, distribution=...)` | `--version` and `--describe`, the command catalogue as JSON |
| `sushicore.diag_commands.register_diagnostic_commands(app, diagnostics, ...)` | `config` and `env` |
| `sushicore.provision.commands.register_provision_commands(app, module)` | `setup`, `doctor`, `link`, `unlink` |
| `sushicore.aliases.AliasTable(program, aliases)` | Old spellings that still run, hidden, and name their replacement |
| `sushicore.entry.run(app, report)` | An entry point that turns a `SushiCoreError` into one line and exit 1; `report` looks the console up when called |

A failure the user can act on derives from `sushicore.errors.SushiCoreError`; anything else
stays a traceback.

## Provisioning

`sushicore.provision` is the dependency root, registry and doctor every module CLI shares.
The root is `SUSHISYSTEMS_HOME`, else `~/.sushisystems`; a consumer overrides it with
`home.bind_root(provider)`. `register_provision_commands(app, module)` adds four commands
(`setup`, `doctor`, `link` and `unlink`) to a Typer app from one `ModuleProvision`, and binds
the module's console through `bind_console` on each call. No module needs hub installed.

```python
import typer
from sushicore.provision.commands import ModuleProvision, register_provision_commands

app = typer.Typer()

module = ModuleProvision(
    profile=PROFILE,
    project_root=lambda: PROJECT_ROOT,
    load_config=load_config,
    console=lambda: console,
)

register_provision_commands(app, module)
```

`setup` installs what the module needs to build and then runs `doctor`. It reads the module's
fragment and, through `[module] depends_on`, the fragment of every module it builds on, found by
the `locate` callable the module passes. A module named there with no checkout stops `setup`
with exit code 2 and one line saying where the checkout belongs; `setup` never clones.

A bare `setup` installs one member of each toolchain capability a fragment marks `required`. When something on the machine
already provides `sycl-toolchain`, nothing downloads; otherwise the first toolchain the fragment
declares for it installs. `--toolchain NAME` adds another and may be repeated. The GPU toolkit
installs when a declared dependency is `gpu_only` and a card is detected; `--no-gpu` skips it.
`--dry-run` shows the run without changing anything, and `--yes` answers the LLVM download
prompt.

`ModuleProvision` takes four optional fields beside the four above:

| Field | Meaning |
| --- | --- |
| `locate` | Finds the checkout of a module `depends_on` names. A `StackConfig` module passes `locate_sibling`. |
| `uses_base` | Adds the shared base fragment (`provision/manifests/base.deps.toml`: gtest, opencl, pkgconf) before the module's own. |
| `panel` | The help panel the commands are listed under. |
| `is_binary` | Reports a binary install, which gets `doctor` alone. |

Toolchains and vcpkg are looked up across `home.search_roots()`: the dependency root first, then
a legacy `<workspace>/dependencies` tree or the one `SUSHISTACK_DEPS_DIR` names. New installs go
to the dependency root. `StackConfig.dependency_roots(root)` puts the tree of the workspace a
module sits in, or is linked to, before those.

`doctor` checks the build tools, the checkouts of the modules this one builds on, the toolchain
capabilities, the fragments and the toolchain stamps; `--for` restricts the report to one group
(`build`, `test`, `infer`, `eval`) and exits 2 on any other. `link` and `unlink` take
`--workspace` to name the workspace registry explicitly.

`link` records the module in the workspace's `[modules]` table and writes a `[link] workspace`
pointer into the module's `cli/config.local.toml`; `unlink` removes both. Linking copies nothing:
config loading follows the pointer and layers the linked workspace's `[tool]` table at read time.
`SUSHISTACK_HOME` still wins over the pointer, and a pointer to a deleted workspace is ignored.

The manual is in `docs/README.md`.

## Licence

SushiCore is source-available, free for non-commercial use under the PolyForm Noncommercial
License 1.0.0; commercial use needs a licence from Sushi Systems, see `COMMERCIAL.md`. `LICENSE`
is the binding text and `NOTICE.md` lists the third-party software.

Versions 0.1.0 to 0.4.0, on PyPI and tagged `v0.1.0` to `v0.4.0`, and the commits up to `9c0fce1`
on GitHub, which carry 0.5.0 and 0.6.0, were published under the Apache License 2.0 and stay
available under it. Every commit before the one that adds `NOTICE.md` carries the Apache License
2.0 text; that commit and every later one are under the licence above, and 0.7.0, when it is
released from such a commit, is the first version under it.

Contributions from outside Sushi Systems are not accepted yet.
