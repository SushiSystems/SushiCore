# Changelog

## Unreleased

## v0.14.1 — 2026-11-16

- 2026-11-16 — checking: Pruned git-ignored folders before walking them in the comment and probe checkers, so a large ignored tree costs no time (RW-84, `ignored_paths.py`).
- 2026-11-16 — shared_tools: Wrote the header the target's settings build on a shared Python file it did not hold, not upstream's open block (RW-83, `header_merger.py`).
- 2026-11-16 — shared_tools: Left `check_package_layers.py` and `check_config_reads.py`, which read SushiCore's own packages, out of the shared set (RW-82, `sync_service.py`).

