# Changelog

## Unreleased

## v0.13.2 — 2026-11-11

- 2026-11-11 — build: Ran a tree's regeneration before the dry run of `CMakeDriver.tree_is_current` and left it out of the dry run, so a tree with `CONFIGURE_DEPENDS` globs reads as current (RW-78, `cmake_driver.py`).
