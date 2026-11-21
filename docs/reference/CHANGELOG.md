# Changelog

## Unreleased

## v0.15.1 — 2026-11-21

- 2026-11-21 — tools: Wrote the index to the pre-commit folder byte for byte, without line-ending conversion, so a repository with `core.autocrlf` matches the lock of the shared tools (RW-149, `pre_commit.py`).
- 2026-11-21 — tools: Linked each submodule the index names into the pre-commit folder and unlinked it after the checks, so a checker that reads `third_party/` finds it (RW-149, `pre_commit.py`).
- 2026-11-21 — tools: Gave the amend test of the commit-msg hook a `Tests:` line, so the shared test passes in a repository that sets `K_TESTS_LINE` (`test_commit_msg.py`).
- 2026-11-21 — tree_reuse: Added `refuse_unreusable_tree`, which refuses a tree of another generator or source folder and names `clean`, and `configured_generator` on the driver port.
