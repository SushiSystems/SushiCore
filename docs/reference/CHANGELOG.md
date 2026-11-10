# Changelog

## Unreleased

- 2026-11-11 — testing: Failed a passing run of a current tree that breaks a time limit, judging each test over a limit by its time when run again alone (RW-78, `budget.py`).
- 2026-11-11 — testing: Handed CTest a resource file with one slot per accelerator, and ran the shards that declare `RESOURCE_GROUPS` one after another in a filtered run, so two never share a device (RW-78, `accelerator_slots.py`).
- 2026-11-11 — build: Added `CMakeDriver.tree_is_current`, a dry run of a Ninja tree that tells a CLI whether the times of a run are the code's (RW-78, `cmake_driver.py`).

## v0.12.4 — 2026-11-10

- 2026-11-10 — tools: Dropped the files below an ignored folder link on Linux, where git lists a symlink to a folder as a file (KI-28, `ignored_paths.py`).
- 2026-11-10 — provision: Split the Windows PATH on a semicolon on every platform, where it cut each drive letter on Linux (KI-29, `base.py`).
- 2026-11-10 — describe: Read a parameter's type from a Typer release that has no Click type objects, so `--describe` and the help page work on Typer 0.27 and later (KI-30, `param_type.py`).
