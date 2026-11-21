# Changelog

## Unreleased

- 2026-11-21 — tools: Showed a finding below a link inside the root, such as a submodule, as a path below the root, so the known findings of its files match in the pre-commit folder (RW-151, `checker.py`).
## v0.15.2 — 2026-11-21

- 2026-11-21 — shared_tools: Hashed each file of the lock with CRLF read as LF, in `digest` and in `check_shared_tools.py`, so a checkout that converts line endings still matches the lock (RW-150).
