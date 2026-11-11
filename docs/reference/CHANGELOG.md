# Changelog

## Unreleased

- 2026-11-11 — build: Let `CMakeDriver.tree_is_current` narrow its dry run to the targets a CLI builds, so a tree built by target reads as current (RW-78, `cmake_driver.py`).

## v0.13.0 — 2026-11-11

- 2026-11-11 — testing: Failed a passing run of a current tree that breaks a time limit, judging each test over a limit by its time when run again alone (RW-78, `budget.py`).
- 2026-11-11 — testing: Handed CTest a resource file with one slot per accelerator, and ran the shards that declare `RESOURCE_GROUPS` one after another in a filtered run, so two never share a device (RW-78, `accelerator_slots.py`).
- 2026-11-11 — build: Added `CMakeDriver.tree_is_current`, a dry run of a Ninja tree that tells a CLI whether the times of a run are the code's (RW-78, `cmake_driver.py`).
