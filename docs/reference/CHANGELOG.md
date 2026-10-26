# Changelog

## Unreleased

## v0.9.7 — 2026-10-26

- 2026-10-26 — provision: Added the `libraries` keyword to `StackConfig.sushi_packages`, which resolves only the named libraries and their closure (`stack_config.py`).
- 2026-10-26 — provision: Added `PackageSet.left_out`, the closure libraries a filter skipped, which `sushi_definitions` leaves without a `-D<NAME>_DIR` (`package_set.py`).
