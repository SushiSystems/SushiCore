# Changelog

## Unreleased

- 2026-11-10 — config: Added the `Environment` port, so appearance and module config load from an in-memory environment and files, and default to the process and the disk (RW-77, `environment.py`).
- 2026-11-10 — testing: Read the shard registrations of a multi-config build tree, whose test file indents each test under its configuration (`shard_registrations.py`).

## v0.12.2 — 2026-11-10

- 2026-11-10 — testing: Added `ProgramRunner`, which runs a test program by the name its shards carry, for a CLI to hand `ModuleTests` as `run_program` (`program_runner.py`, `shards.py`).
- 2026-11-10 — commands: Let the test filter narrow a sharded build whose shards pass their own --gtest_filter (RW-74, `cd2b5ff`).
