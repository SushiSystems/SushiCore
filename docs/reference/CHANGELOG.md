# Changelog

## Unreleased

- 2026-10-20 — docs: Moved 8 known issues with a scheduled fix and no workaround into the backlog entries that fix them (`KNOWN_ISSUES.md`, `REMAINING_WORK.md`).
- 2026-10-19 — docs: Moved the backlog and the known issues to the SushiSkills entry format and took the backlog checker with the shared tools (`REMAINING_WORK.md`, `KNOWN_ISSUES.md`, `check_backlog.py`).
- 2026-10-18 — docs: Cut the root README to the six sections of the documentation skill, and added the shared Code of Conduct and security policy (`README.md`, `.github/`).

## v0.9.2 — 2026-10-17

- 2026-10-17 — provision: Skipped the Visual Studio Build Tools install when any Visual Studio with the C++ tools is found, so setup passes on a CI runner without winget (`steps.py`).
