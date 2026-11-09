# Changelog

## Unreleased

## v0.12.0 — 2026-11-10

- 2026-11-10 — testing: Emptied `test_results/gtest` before a run and handed the folder to the budget reader as `--cases` (`session.py`, `budget.py`).
- 2026-11-10 — testing: Passed `--filter` to every shard as `GTEST_FILTER` over a sharded build (`session.py`, `cmake_driver.py`).
- 2026-11-10 — testing: Reran a failed shard's failing cases by `--gtest_filter` through `ModuleTests.run_program`, and reported a pass on rerun as flaky (`rerun.py`).
- 2026-11-10 — testing: Reran a failed test of an unsharded build by `ctest -R` and handed the budget reader the rerun results (`rerun.py`, `session.py`).
- 2026-11-10 — testing: Counted a small-only run at 256 MB per test in the job count, so it takes every core (`job_count.py`).
- 2026-11-10 — testing: Took `test_budget.py` with `--cases` and a `--rerun` folder from SushiSkills commit `219b191` (`test_budget.py`).
