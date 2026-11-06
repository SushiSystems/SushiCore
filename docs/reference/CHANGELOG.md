# Changelog

## Unreleased

- 2026-11-07 — testing: Added a CMake driver port, which the disk driver keeps with two new tree reads, and an in-memory driver that passes the same contract test (RW-69, `cmake_driver_memory.py`).

- 2026-11-07 — continuous_integration: Deleted the budget-settings checker test that SushiSkills dropped, since it only skipped here (RW-68, `a528a1d`).

## v0.10.14 — 2026-11-07

- 2026-11-07 — help: Imported Click only for type checking again and found Click's plain help through the command's bases, so a CLI on Typer 0.27, which ships its own Click, starts again (`typer_help.py`).
- 2026-11-07 — testing: Gave `CommandRunner.capture` an optional `timeout`, which ends the command with exit code 124; `RecordingRunner` records it and can script a timeout (`proc.py`, `proc_memory.py`).
- 2026-11-07 — continuous_integration: Cleared the known findings of the shared checkers (RW-64, `f3088f0`).
- 2026-11-07 — console: Gave `PlainRenderer` an optional `input_stream`, which its prompt reads instead of `input()`, as `JsonRenderer` does (`renderer.py`).
- 2026-11-07 — provision: Matched a whole package ID in `WingetManager.is_installed`, so `Git.G` no longer reads as installed (`packages/winget.py`).
- 2026-11-07 — provision: Read the toolchain stamp as UTF-8 on every platform (`toolchains/stamp.py`).
- 2026-11-07 — help: Printed Click's plain help, and logged why, when Typer's own help fails too, as on a stray close tag, so `--help` never crashes (`typer_help.py`).
- 2026-11-07 — testing: Add the `Files` port with its disk and in-memory adapters, and let the backlog and design stores take one, so their logic is tested with no disk (`files.py`, `files_memory.py`, `backlog/store.py`, `design/store.py`).
- 2026-11-07 — tools: Delete the test-addition checker and its tests (`tools/testing/check_test_additions.py`).
