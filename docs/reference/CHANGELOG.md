# Changelog

## Unreleased

- 2026-11-07 — testing: Add the `Files` port with its disk and in-memory adapters, and let the backlog and design stores take one, so their logic is tested with no disk (`files.py`, `files_memory.py`, `backlog/store.py`, `design/store.py`).
- 2026-11-07 — tools: Delete the test-addition checker and its tests (`tools/testing/check_test_additions.py`).

## v0.10.13 — 2026-11-06

- 2026-11-06 — testing: Put `capture` on the `CommandRunner` port and the recording runner, which records it and answers scripted stdout and stderr (`proc.py`, `proc_memory.py`).
