# Changelog

## Unreleased

## v0.12.4 — 2026-11-10

- 2026-11-10 — tools: Dropped the files below an ignored folder link on Linux, where git lists a symlink to a folder as a file (KI-28, `ignored_paths.py`).
- 2026-11-10 — provision: Split the Windows PATH on a semicolon on every platform, where it cut each drive letter on Linux (KI-29, `base.py`).
- 2026-11-10 — describe: Read a parameter's type from a Typer release that has no Click type objects, so `--describe` and the help page work on Typer 0.27 and later (KI-30, `param_type.py`).
