# Changelog

## Unreleased

- 2026-10-30 — repository: Added `.gitattributes` and `.editorconfig`, finished `.gitignore` and made CI fetch full history (RW-19, `ca7b342`).
## v0.10.5 — 2026-10-29

- 2026-10-29 — build_gate: Fixed the kernel check failing a host unit of a `-g` build whose debug information names a `single_task` it only references; it reads the symbols the ELF64 or COFF object defines (`build_gate.py`).
- 2026-10-29 — sushi_packages: Fixed a nested package build recompiling the whole library whenever a package below it changed; a handed-down package reaches its flags through a stable link, not its digest folder (`package_resolver.py`).
