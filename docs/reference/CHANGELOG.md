# Changelog

## Unreleased

- 2026-11-10 — testing: Emptied `test_results/gtest` before a run and handed the folder to the budget reader as `--cases` (`session.py`, `budget.py`).
- 2026-11-10 — testing: Passed `--filter` to every shard as `GTEST_FILTER` over a sharded build (`session.py`, `cmake_driver.py`).
- 2026-11-10 — testing: Reran a failed shard's failing cases by `--gtest_filter` through `ModuleTests.run_program`, and reported a pass on rerun as flaky (`rerun.py`).
- 2026-11-10 — testing: Reran a failed test of an unsharded build by `ctest -R` and handed the budget reader the rerun results (`rerun.py`, `session.py`).
- 2026-11-10 — testing: Counted a small-only run at 256 MB per test in the job count, so it takes every core (`job_count.py`).
- 2026-11-10 — testing: Took `test_budget.py` with `--cases` and a `--rerun` folder from SushiSkills commit `219b191` (`test_budget.py`).

## v0.11.0 — 2026-11-10

- 2026-11-10 — provisioning: Changed `ModuleProvision` to take one `MachineSeams` value in place of its three builders; callers pass `seams` (`module_provision.py`).
- 2026-11-10 — testing: Moved `free_memory_mb` and its reserve constant out of `build_gate.py` into `memory_reading.py`, which the gate and the test job count both read.
- 2026-11-10 — testing: Made `test` run one job per core, lowered to fit the free memory, when no `--jobs` is given, and print the count (R1, `job_count.py`).
- 2026-11-10 — provisioning: Fixed 11 provision tests that failed on Windows: the migration plan reads the working directory by probe, and a configured library directory naming no folder yields to the variable (KI-27, `5f66b8f`).
- 2026-11-07 — continuous_integration: Gave the Files port a remove call and routed the backlog check, close and merge through it, so their small tests read no disk (RW-70, `f44d1ef`).
