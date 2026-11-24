# Changelog

## Unreleased

- 2026-11-24 — tools: Added `check_sushicore_pin.py`, which refuses an upper bound on the sushicore requirement, so CLIs installed side by side cannot clash on it (`tools/checking/check_sushicore_pin.py`, RW-168).

## v0.17.1 — 2026-11-24

- 2026-11-24 — testing: Fixed the slow and failed case reruns starting a shard's program without the arguments, environment and timeout the shard registers (`source/sushicore/testing/shard_case_run.py`).
