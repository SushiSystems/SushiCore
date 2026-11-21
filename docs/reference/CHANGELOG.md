# Changelog

## Unreleased

## v0.15.4 — 2026-11-21

- 2026-11-21 — code: Checked the staged tree beside the repository, with the ignored files on disk (RW-152, `tools/hooks/pre_commit.py`).
- 2026-11-21 — releases: Found that v0.14.0 and v0.14.1 were never pushed, so no release workflow ran; the two local tags are deleted and 0.15.0 to 0.15.3 are on PyPI (RW-146).
- 2026-11-21 — provisioning: Built the Linux manager plan when the run hands it a download verifier, so `hub install` and `module_provision` no longer fail on Linux (RW-153, `manager_plans/linux.py`).
