# Changelog

## Unreleased

- 2026-11-23 — cmake: Added `sushi_sycl_source_options`, which gives device options the form a source file's `COMPILE_OPTIONS` takes; `sushi_sycl_target` uses it (`SushiSyclTarget.cmake`).
- 2026-11-23 — cmake: Fixed a link to a tier module declared later passing as a plain item; `sushi_tier_module` now stops the configure and names the targets that linked it first (`SushiTierLibraries.cmake`).
- 2026-11-23 — testing: Indexed the file lists of the test mirror checker once instead of scanning the tree for each module, so a full run on SushiEngine drops from over 60 s to about 3 s (`tools/testing/check_test_mirror.py`).
- 2026-11-23 — provision: Added the llvm-sycl licence texts under `share/licenses/llvm-sycl/<component>/`; `install_intel_llvm` and the adapter build fail without them (`toolchain_licence.py`).
- 2026-11-23 — testing: Added budget exemptions that hold only on the platforms they name, `{ id = "RW-12", platforms = ["linux"] }` (`tools/testing/test_budget.py`).
- 2026-11-23 — documentation: Fixed the docs truth checker skipping cited paths under `tools/build/`, which are source and are now checked (`tools/documentation/check_docs_truth.py`).

## v0.16.2 — 2026-11-23

- 2026-11-22 — testing: Fixed the slow and failed shard reruns finding no executable when CMake writes a test name in quotes instead of brackets (`source/sushicore/testing/shards.py`, `shard_registrations.py`).
