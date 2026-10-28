# Changelog

## Unreleased

## v0.10.1 — 2026-10-28

- 2026-10-28 — design: Stopped a topic under `_REVISION/` from owning a module, so a frozen topic no longer blocks the live one that took its modules over (`store.py`).
- 2026-10-28 — design: Made `--json` of both groups write ASCII escapes, so a Windows console in a legacy code page can pipe it (`commands.py`).
- 2026-10-28 — backlog: Made `import` rewrite only Markdown pages, the docs-relative citations among them, and list the source files that name a retired file (`importer.py`).
