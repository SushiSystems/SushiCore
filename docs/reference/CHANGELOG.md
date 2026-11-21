# Changelog

## Unreleased

- 2026-11-22 — commands: Stopped judging a sanitized `test` run by the time limits, which a sanitizer makes several times slower, and said so in a line (`testing/session.py`).
- 2026-11-22 — commands: Left a rerun folder that no rerun wrote out of the budget reader's command, so a test that fails again alone no longer ends the run with the reader's `FileNotFoundError` (RW-155, `testing/budget.py`).

## v0.15.5 — 2026-11-22

- 2026-11-21 — downloads: Renewed the digests of the intel/llvm nightly bundle, whose assets intel re-uploaded after they were pinned, so `sr setup` and `sa setup` stop on a mismatch no more (RW-154, `manifests/base.deps.toml`).
