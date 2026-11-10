# Changelog

## Unreleased

## v0.12.2 — 2026-11-10

- 2026-11-10 — testing: Added `ProgramRunner`, which runs a test program by the name its shards carry, for a CLI to hand `ModuleTests` as `run_program` (`program_runner.py`, `shards.py`).
- 2026-11-10 — commands: Let the test filter narrow a sharded build whose shards pass their own --gtest_filter (RW-74, `cd2b5ff`).
