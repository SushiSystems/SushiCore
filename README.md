# SushiCore

The shared library under the Sushi developer CLIs (`hub`, `sr`, `se`, `sa`, `sb`, `sd`, `st`):
workspace lookup, layered TOML configuration, terminal and JSON output, help screens, the cmake
and ctest driver, and the `setup` and `doctor` provisioning every module CLI registers.

```python
import typer

from sushicore.entry import run

app = typer.Typer(name="sx", no_args_is_help=True)


@app.command("build")
def build() -> None:
    """Configure and build."""


run(app, report=print)
```

Source: not compiled

`run` turns any error sushicore raises into one line and exit code 1.

## Build

```bash
pip install -e ".[typer]"
python -m pytest
```

## Status

Used by all seven CLIs, which need 0.7.0 or later. Planned work is in
[`docs/backlog/README.md`](docs/backlog/README.md).

## Documentation

The manual starts at [`docs/README.md`](docs/README.md); installing a checkout in place of the
PyPI package is in [`docs/getting_started/INSTALL.md`](docs/getting_started/INSTALL.md).
Contributions from outside Sushi Systems are not accepted yet; [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md)
says how a change lands.

## Licence

Source-available, free for non-commercial use under the PolyForm Noncommercial License 1.0.0;
see `LICENSE`. Commercial use needs a licence from Sushi Systems; see `COMMERCIAL.md`.
Third-party software is listed in `NOTICE.md`. Versions 0.1.0 to 0.6.0, the commits before the
one that adds `NOTICE.md`, stay available under the Apache License 2.0.
