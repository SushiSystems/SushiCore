# Changelog

## Unreleased

- 2026-10-07 — docs: Added the frequently asked questions page (`docs/guides/FAQ.md`).
- 2026-10-07 — docs-bundle: Added the documentation bundle producer and the `docs` command group a CLI registers (`sushicore/docs_bundle/`, `register_docs_commands`, `BundleProducer`).
- 2026-10-07 — describe: Listed a group that runs without a subcommand as a command of its own in the catalogue (`sushicore/describe.py`, `_flatten`).
- 2026-10-07 — cmake: Fixed a configure losing its `-D` values when the compiler path changed, by deleting the tree's cache before the run (`CMakeDriver.configure`, `compiler_changed`, `sushicore/cmake_cache.py`).

## v0.8.0 — 2026-10-07

- 2026-10-07 — provision: Added a journaled dependency-root migration that renames on one volume and copies across two, with rollback and finalize (`sushicore/provision/migrate.py`).
- 2026-10-07 — provision: Added directory links, junctions on Windows and symlinks elsewhere (`sushicore/provision/links.py`).
- 2026-10-07 — provision: Added the reader and writer of the user's persistent environment variables (`sushicore/provision/user_environment.py`).
- 2026-10-07 — provision: Added registry seeding from an existing dependency tree (`Registry.seed_from_tree`, `sushicore/provision/registry.py`).
- 2026-10-07 — licence: Named Mustafa Garip and Sushi Systems as the copyright holders in the licence and notice files (`LICENSE`, `NOTICE.md`).
- 2026-10-06 — licence: Restored the three-section license box and named both holders in the copyright line of every source file (`tools/licensing/write_license_block.py`, `tools/documentation/check_source_comments.py`).
