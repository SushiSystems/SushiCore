# Changelog

## Unreleased

- 2026-11-28 — backlog: Removed `backlog import`, `BacklogImporter`, `ImportResult` and the check for the retired files, deprecated since 0.15.0, which no repository needs now (`backlog/`, RW-133).

## v0.18.5 — 2026-11-28

- 2026-11-28 — tools: Made the pre-commit tree copy the files that match the index instead of hard linking them, which Windows cannot remove while an editor holds them, and link ignored folders like `build/` (`tools/hooks/index_tree.py`).
