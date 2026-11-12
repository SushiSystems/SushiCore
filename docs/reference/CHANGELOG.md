# Changelog

## Unreleased

- 2026-11-12 — aliases: Let `AliasTable` take the stream and the variables its notices use, so a CLI test reads a notice from memory (`aliases.py`).

## v0.13.2 — 2026-11-11

- 2026-11-11 — build: Ran a tree's regeneration before the dry run of `CMakeDriver.tree_is_current` and left it out of the dry run, so a tree with `CONFIGURE_DEPENDS` globs reads as current (RW-78, `cmake_driver.py`).
