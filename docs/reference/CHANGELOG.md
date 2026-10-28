# Changelog

## Unreleased

- 2026-10-28 — build_trace: Added the summary of the clang time traces a build leaves beside its objects: costliest headers, templates and units (`build_trace.py`).
- 2026-10-28 — build_gate: Added `-ftime-trace` for the units listed in `time_trace.txt`, written by `request_time_traces` in `build_admission` (`build_gate.py`, `build_admission.py`).
- 2026-10-28 — provision: Made the package command install the default Debug tree when no build directory is given; it read a tree named build, which no CLI creates now (`package_command.py`).
- 2026-10-28 — build_tree: Added `package_build_type`, the Release packages a Debug, MinSizeRel or sanitized consumer links (`build_tree.py`).
- 2026-10-28 — build_gate: Added the memory gate every compile and link of a tree runs through, with host compiles cached by ccache (`build_gate.py`, `build_admission.py`).
- 2026-10-28 — build_tree: Added one tree per build type, `build/<name>-<type>`, Debug by default, refusing any other type in a tree (`build_tree.py`).
- 2026-10-28 — build_report: Added the report of one build's time and peak memory per kind of edge (`build_report.py`).
- 2026-10-28 — config_base: Added `ccache_exe`, overridden by `<PREFIX>_CCACHE` (`config_base.py`, `profile.py`).
- 2026-10-27 — cmake_driver: Gave the compilers `compiler_tmp` in the build tree as `TMP` and `TEMP` in `compile`, deleted when the build ends (`cmake_driver.py`).
- 2026-10-27 — build_env: Dropped `TMP` and `TEMP` from the vcvars snapshot, so a build honours the caller's scratch folder (`build_env.py`).

## v0.9.7 — 2026-10-26

- 2026-10-26 — provision: Added the `libraries` keyword to `StackConfig.sushi_packages`, which resolves only the named libraries and their closure (`stack_config.py`).
- 2026-10-26 — provision: Added `PackageSet.left_out`, the closure libraries a filter skipped, which `sushi_definitions` leaves without a `-D<NAME>_DIR` (`package_set.py`).
