# Changelog

## v0.18.5 — 2026-11-28

- 2026-11-28 — tools: Made the pre-commit tree copy the files that match the index instead of hard linking them, which Windows cannot remove while an editor holds them, and link ignored folders like `build/` (`tools/hooks/index_tree.py`).
