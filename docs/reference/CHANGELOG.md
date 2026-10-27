# Changelog

## Unreleased

- 2026-10-27 — cmake_driver: `compile` gives the compilers `compiler_tmp` in the build tree as `TMP` and `TEMP`, and deletes it when the build ends (`cmake_driver.py`).
- 2026-10-27 — build_env: Dropped `TMP` and `TEMP` from the vcvars snapshot, so a build honours the caller's scratch folder (`build_env.py`).

## v0.9.7 — 2026-10-26

- 2026-10-26 — provision: Added the `libraries` keyword to `StackConfig.sushi_packages`, which resolves only the named libraries and their closure (`stack_config.py`).
- 2026-10-26 — provision: Added `PackageSet.left_out`, the closure libraries a filter skipped, which `sushi_definitions` leaves without a `-D<NAME>_DIR` (`package_set.py`).
