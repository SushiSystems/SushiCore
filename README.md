# SushiCore

The shared core of the Sushi developer CLIs. `hub`, `sr`, `se`, `sa`, `sb`, `sd` and `st` all
import it to locate a workspace, load layered TOML configuration, print to a terminal or to a
JSON stream, draw their help screens, drive cmake and ctest, and install and check what a
repository needs to build.

It is a library for those CLIs and installs no console script. It knows nothing about SYCL, a
renderer, or any one module's schema.

```bash
pip install "sushicore[typer]"
```

PyPI carries 0.4.0. The seven CLIs need 0.7.0, which is not released yet;
[Installing](docs/getting_started/INSTALL.md) says how to install it from a checkout.

| To read about | Open |
| --- | --- |
| Everything, from one index | [The manual](docs/README.md) |
| What each module of the package does | [Architecture overview](docs/architecture/OVERVIEW.md) |
| Wiring a CLI to the shared surfaces | [CLI integration](docs/guides/CLI_INTEGRATION.md) |
| `setup`, `doctor`, `link` and `unlink` | [`sushicore/provision/README.md`](sushicore/provision/README.md) |
| Terminal components and tables | [`sushicore/ui/README.md`](sushicore/ui/README.md) |
| The help screen | [`sushicore/help/README.md`](sushicore/help/README.md) |

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
