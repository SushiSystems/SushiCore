# Changelog

## Unreleased

- 2026-10-28 — docs: Moved the backlog and the known issues into `docs/backlog/` with `backlog import` (`docs/backlog/`).
- 2026-10-28 — design: Added the `design` group, which opens topics, pages and phases, refuses a module another topic owns, and lists and merges overlapping topics (`sushicore.design`).
- 2026-10-28 — backlog: Added the `backlog` group, which keeps remaining work and known issues as tables in `docs/backlog/` and computes the order of `next` (`sushicore.backlog`).
- 2026-10-28 — citations: Added the finding and rewriting of citations of a moved document or a renamed ID (`citations.py`).
## v0.9.8 — 2026-10-28

- 2026-10-28 — test: Made the path and the link-swap tests of provision hold on every runner, after v0.9.7 failed its gate (`test_consumer_build.py`, `test_stable_link.py`).
- 2026-10-28 — build_gate: Lowered the reservation of a device link no build has measured from 3000 to 1500 MB, measured links having peaked at 1156 MB, so links run side by side (`build_gate.py`).
- 2026-10-28 — build_gate: Failed a host compile whose object instantiates a SYCL kernel submission, which would lose its kernel at run time (`build_gate.py`).
- 2026-10-28 — build_trace: Added the summary of the clang time traces a build leaves beside its objects: costliest headers, templates and units (`build_trace.py`).
- 2026-10-28 — build_gate: Added `-ftime-trace` to the compiles of the units a build requests through `request_time_traces` (`build_gate.py`).
- 2026-10-28 — provision: Made the package command install the default Debug tree when no build directory is given; it read a tree named build, which no CLI creates now (`package_command.py`).
- 2026-10-28 — build_tree: Added `package_build_type`, the Release packages a Debug, MinSizeRel or sanitized consumer links (`build_tree.py`).
- 2026-10-28 — build_gate: Added the memory gate every compile and link of a tree runs through, with host compiles cached by ccache (`build_gate.py`, `build_admission.py`).
- 2026-10-28 — build_tree: Added one tree per build type, `build/<name>-<type>`, Debug by default, refusing any other type in a tree (`build_tree.py`).
- 2026-10-28 — build_report: Added the report of one build's time and peak memory per kind of edge (`build_report.py`).
- 2026-10-28 — config_base: Added `ccache_exe`, overridden by `<PREFIX>_CCACHE` (`config_base.py`, `profile.py`).
- 2026-10-27 — cmake_driver: Gave the compilers `compiler_tmp` in the build tree as `TMP` and `TEMP` in `compile`, deleted when the build ends (`cmake_driver.py`).
- 2026-10-27 — build_env: Dropped `TMP` and `TEMP` from the vcvars snapshot, so a build honours the caller's scratch folder (`build_env.py`).
- 2026-10-26 — provision: Added the `libraries` keyword to `StackConfig.sushi_packages`, which resolves only the named libraries and their closure (`stack_config.py`).
- 2026-10-26 — provision: Added `PackageSet.left_out`, the closure libraries a filter skipped, which `sushi_definitions` leaves without a `-D<NAME>_DIR` (`package_set.py`).
