# Changelog

## Unreleased

- 2026-11-11 — build: Ran a tree's regeneration before the dry run of `CMakeDriver.tree_is_current` and left it out of the dry run, so a tree with `CONFIGURE_DEPENDS` globs reads as current (RW-78, `cmake_driver.py`).

## v0.13.1 — 2026-11-11

- 2026-11-11 — build: Let `CMakeDriver.tree_is_current` narrow its dry run to the targets a CLI builds, so a tree built by target reads as current (RW-78, `cmake_driver.py`).
