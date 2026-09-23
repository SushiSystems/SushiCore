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

## Provisioning

`sushicore.provision` is the dependency root, registry and doctor every module CLI shares.
The root is `SUSHISYSTEMS_HOME`, else `~/.sushisystems`; a consumer overrides it with
`home.bind_root(provider)`. `register_provision_commands(app, module)` adds four commands —
`setup`, `doctor`, `link` and `unlink` — to a Typer app from one `ModuleProvision`, and binds
the module's console through `bind_console` on each call.

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

`setup` takes `--dry-run` and `--yes`; `doctor` takes `--for` to restrict the report to one
check group; `link` and `unlink` take `--workspace` to name the workspace registry explicitly.

The manual is in `docs/README.md`. Licensed under the terms in `LICENSE`.
