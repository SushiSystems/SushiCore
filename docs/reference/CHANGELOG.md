# Changelog

## Unreleased

## v0.13.4 — 2026-11-14

- 2026-11-14 — testing: Made a rerun that finds no executable say what the test files hold, the files read and the `add_test` lines that name the program (`shards.py`, `slow_rerun.py`).
- 2026-11-14 — testing: Made `SlowTestRerun` name a rerun that wrote no result file and hand the reader only a folder that exists, so a missing rerun folder no longer crashes the time-limit gate (`slow_rerun.py`).
