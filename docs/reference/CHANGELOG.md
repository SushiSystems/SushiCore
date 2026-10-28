# Changelog

## Unreleased

- 2026-10-28 — backlog: Made `import` rewrite only Markdown pages, the docs-relative citations among them, and list the source files that name a retired file (`importer.py`).

## v0.10.0 — 2026-10-28

- 2026-10-28 — docs: Moved the backlog and the known issues into `docs/backlog/` with `backlog import` (`docs/backlog/`).
- 2026-10-28 — design: Added the `design` group, which opens topics, pages and phases, refuses a module another topic owns, and lists and merges overlapping topics (`sushicore.design`).
- 2026-10-28 — backlog: Added the `backlog` group, which keeps remaining work and known issues as tables in `docs/backlog/` and computes the order of `next` (`sushicore.backlog`).
- 2026-10-28 — citations: Added the finding and rewriting of citations of a moved document or a renamed ID (`citations.py`).
