# Changelog

## Unreleased

## v0.15.2 — 2026-11-21

- 2026-11-21 — shared_tools: Hashed each file of the lock with CRLF read as LF, in `digest` and in `check_shared_tools.py`, so a checkout that converts line endings still matches the lock (RW-150).
