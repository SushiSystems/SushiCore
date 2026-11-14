# Changelog

## Unreleased

- 2026-11-14 — testing: Made `SlowTestRerun` name a rerun that wrote no result file and hand the reader only a folder that exists, so a missing rerun folder no longer crashes the time-limit gate (`slow_rerun.py`).

## v0.13.2 — 2026-11-11

- 2026-11-11 — build: Ran a tree's regeneration before the dry run of `CMakeDriver.tree_is_current` and left it out of the dry run, so a tree with `CONFIGURE_DEPENDS` globs reads as current (RW-78, `cmake_driver.py`).
