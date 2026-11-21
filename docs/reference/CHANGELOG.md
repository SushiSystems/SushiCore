# Changelog

## Unreleased

- 2026-11-22 — commands: Linked a Linux configure with lld when its clang or icpx compiler has it, and said so in a line, unless the configure chose a linker (RW-156, `lld_linker.py`).
## v0.15.6 — 2026-11-22

- 2026-11-22 — commands: Stopped judging a sanitized `test` run by the time limits, which a sanitizer makes several times slower, and said so in a line (`testing/session.py`).
- 2026-11-22 — commands: Left a rerun folder that no rerun wrote out of the budget reader's command, so a test that fails again alone no longer ends the run with the reader's `FileNotFoundError` (RW-155, `testing/budget.py`).
