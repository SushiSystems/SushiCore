# sushicore

The shared core of the Sushi developer CLIs. `hub`, `sr`, `se`, `sa`, `sb`, `sd` and `st` all
import it for the same four things: locating a workspace, loading layered TOML configuration,
printing to a terminal or to a JSON stream, and driving cmake and ctest.

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
| `sushicore.cmake_driver`, `cmake_cache`, `proc`, `toolchain_args` | The configure, build and test driver the CLIs share |

The manual is in `docs/README.md`. Licensed under the terms in `LICENSE`.
