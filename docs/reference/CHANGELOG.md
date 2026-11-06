# Changelog

## Unreleased

## v0.10.15 — 2026-11-07

- 2026-11-07 — testing: Added `TerminalMemoryRenderer`, an in-memory terminal a help page can be drawn on (`renderer.py`).
- 2026-11-07 — testing: Gave the stack config, the TOML writer, the console switch, the Typer theme and the help group optional seams whose defaults keep today's behaviour (`typer_help.py`).

- 2026-11-07 — testing: Gave the alias table, the build gate, the trace summary, the icon registry, the diagnostics and the TOML reader optional seams whose defaults keep today's behaviour, so their tests run small (`build_gate.py`).

- 2026-11-07 — testing: Added a CMake driver port, which the disk driver keeps with two new tree reads, and an in-memory driver that passes the same contract test (RW-69, `cmake_driver_memory.py`).

- 2026-11-07 — continuous_integration: Deleted the budget-settings checker test that SushiSkills dropped, since it only skipped here (RW-68, `a528a1d`).
