# Changelog

## Unreleased

## v0.10.16 — 2026-11-13

- 2026-11-13 — tools: Dropped the files below an ignored folder link on POSIX, as on Windows, so the 0.10 line passes its release checks and reaches PyPI (`ignored_paths.py`).
- 2026-11-13 — deps: Held Typer below 0.27, whose own parser gives a parameter no Click type that `describe` reads on this line (`pyproject.toml`).
