# Changelog

## Unreleased

- 2026-11-24 — testing: Fixed the slow and failed case reruns starting a shard's program without the arguments, environment and timeout the shard registers (`source/sushicore/testing/shard_case_run.py`).

## v0.17.0 — 2026-11-24

- 2026-11-23 — provision: Fixed a new package install restamping every file, which made a consumer rebuild everything; files equal to the previous package keep its time (`timestamp_carrier.py`, `package_resolver.py`).
- 2026-11-23 — cmake: Added `sushi_sycl_source_options`, which gives device options the form a source file's `COMPILE_OPTIONS` takes; `sushi_sycl_target` uses it (`SushiSyclTarget.cmake`).
- 2026-11-23 — cmake: Fixed a link to a tier module declared later passing as a plain item; `sushi_tier_module` now stops the configure and names the targets that linked it first (`SushiTierLibraries.cmake`).
- 2026-11-23 — testing: Indexed the file lists of the test mirror checker once instead of scanning the tree for each module, so a full run on SushiEngine drops from over 60 s to about 3 s (`tools/testing/check_test_mirror.py`).
- 2026-11-23 — provision: Added the llvm-sycl licence texts under `share/licenses/llvm-sycl/<component>/`; `install_intel_llvm` and the adapter build fail without them (`toolchain_licence.py`).
- 2026-11-23 — testing: Added budget exemptions that hold only on the platforms they name, `{ id = "RW-12", platforms = ["linux"] }` (`tools/testing/test_budget.py`).
- 2026-11-23 — documentation: Fixed the docs truth checker skipping cited paths under `tools/build/`, which are source and are now checked (`tools/documentation/check_docs_truth.py`).
