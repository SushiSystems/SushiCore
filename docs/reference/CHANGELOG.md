# Changelog

## Unreleased

- 2026-11-23 — testing: Added budget exemptions that hold only on the platforms they name, `{ id = "RW-12", platforms = ["linux"] }` (`tools/testing/test_budget.py`).

## v0.16.2 — 2026-11-23

- 2026-11-22 — testing: Fixed the slow and failed shard reruns finding no executable when CMake writes a test name in quotes instead of brackets (`source/sushicore/testing/shards.py`, `shard_registrations.py`).
