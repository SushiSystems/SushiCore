# Changelog

## Unreleased

## v0.9.5 — 2026-10-26

- 2026-10-26 — tools: Took the shared tools from SushiSkills, so the design-topic tests pass on a Windows runner and the release reaches PyPI (`tools/`).
- 2026-10-26 — provision: Renamed the pin tables of a dependency fragment to `[sushisystems.<name>]`; `[sushi.<name>]` still reads, with a `DeprecationWarning`, and a file holding both is refused (`deps_fragment.py`).
- 2026-10-21 — docs: Gave the three design documents the five design sections and a phase table, moved the GPU run evidence to a work folder, and took the design format checker (`GPU_TOOLKIT_SELECTION.md`).
- 2026-10-20 — docs: Moved 8 known issues with a scheduled fix and no workaround into the backlog entries that fix them (`KNOWN_ISSUES.md`, `REMAINING_WORK.md`).
- 2026-10-19 — docs: Moved the backlog and the known issues to the SushiSkills entry format and took the backlog checker with the shared tools (`REMAINING_WORK.md`, `KNOWN_ISSUES.md`, `check_backlog.py`).
- 2026-10-18 — docs: Cut the root README to the six sections of the documentation skill, and added the shared Code of Conduct and security policy (`README.md`, `.github/`).
