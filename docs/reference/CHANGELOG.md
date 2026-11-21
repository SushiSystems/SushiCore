# Changelog

## Unreleased

- 2026-11-21 — code: Checked the staged tree beside the repository, with the ignored files on disk (RW-152, `tools/hooks/pre_commit.py`).
- 2026-11-21 — releases: Found that v0.14.0 and v0.14.1 were never pushed, so no release workflow ran; the two local tags are deleted and 0.15.0 to 0.15.3 are on PyPI (RW-146).
- 2026-11-21 — provisioning: Built the Linux manager plan when the run hands it a download verifier, so `hub install` and `module_provision` no longer fail on Linux (RW-153, `manager_plans/linux.py`).

## v0.15.3 — 2026-11-21

- 2026-11-21 — tools: Showed a finding below a link inside the root, such as a submodule, as a path below the root, so the known findings of its files match in the pre-commit folder (RW-151, `checker.py`).
