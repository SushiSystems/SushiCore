# Installing

SushiCore is a Python library, published on PyPI as `sushicore`. It needs Python 3.10 or later
and installs no console script.

## From PyPI

```bash
pip install sushicore            # workspace, configuration, console, cmake driver
pip install "sushicore[typer]"   # the same, plus Typer
```

Typer is an optional extra. A CLI that uses `help_group`, the root options, the diagnostic
commands or the provisioning commands needs it; `import sushicore` alone does not.

PyPI carries the tags the release workflow published, not every tag; `pip index versions sushicore`
lists them. All seven Sushi CLIs require `sushicore>=0.7.0`.

## From a checkout

```bash
git clone https://github.com/SushiSystems/SushiCore
cd SushiCore
pip install -e ".[typer]"
```

A CLI installed with pipx has its own environment. Install the checkout into that environment
to make the CLI use it:

```bash
pipx inject --editable <cli-package> /path/to/SushiCore
```

## Running the tests

```bash
pip install -e ".[test]"
python -m pytest tests -q
```

The `test` extra adds pytest, pytest-timeout, Typer and Click. CI runs the tests job,
`python -m pytest -q -m "(small or medium) and not quarantined"`, on Ubuntu and Windows with Python 3.10 and 3.11,
and the `checks` job, `python tools/check_all.py .`, on Ubuntu and Windows with Python 3.11 (`.github/workflows/ci.yml`).

## Running the checkers

The checkers under `tools/` read the repository and change no file of it; after a clean run `check_all.py` writes the commit it checked to `.git/sushicore/verified`. They need Python 3.11.

```bash
python tools/documentation/check_docs_layout.py .
python tools/documentation/check_changelog.py .
python tools/documentation/check_source_comments.py .
python tools/layering/check_layering.py .
python -m unittest discover -s tools/tests
```

[`tools/README.md`](../../tools/README.md) says what each one checks.

## Releasing

`.github/workflows/release.yml` builds the package and publishes it to PyPI when a tag named
`v*` is pushed. The tag is the release; a version number in `pyproject.toml` without a tag
publishes nothing.
