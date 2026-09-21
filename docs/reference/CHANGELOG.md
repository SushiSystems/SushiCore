# Changelog

One line per meaningful change, newest first. Format: date, a past-tense verb, what changed, and
where, in backticks. No why; the reason lives in a design document the entry may link.

- 2026-09-22 — Moved the workspace contract into `workspace.py`: the marker, `workspace.toml` and the pre-2026-09-22 shared-config path (`sushicore/workspace.py`, `sushicore/module_config.py`).
- 2026-09-22 — Removed `WORKSPACE_CLI_DIR`, which named another repository's source layout (`sushicore/workspace.py`).
- 2026-09-22 — Kept sibling tables when writing `[tool]`, so one file can hold more than one section (`sushicore/config_base.py`).
- 2026-09-22 — Published 0.1.0 to PyPI from its own repository (`.github/workflows/release.yml`).
- 2026-09-22 — Split the package out of SushiStack with its own history (`git subtree split`).
