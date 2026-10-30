# Changelog

## Unreleased

- 2026-10-30 — command_line: Ended every provisioning command with one result event, through the outcome the commands return (RW-37, KI-5, `d63deb6`).
- 2026-10-30 — command_line: Made link refuse a path without the workspace marker and put the old link back when the registry write fails (RW-39, KI-8, `d63deb6`).
- 2026-10-30 — code: Moved the bodies of the four provisioning commands out of the module that registers them (RW-21, `d63deb6`).
- 2026-10-30 — downloads: Recorded why a failed probe found no Visual Studio instead of returning nothing in silence (RW-47, KI-18, `617a61d`).
- 2026-10-30 — commands: Reported a build tree that survived `clean` as a failure instead of as removed (RW-43, KI-12, `efb6ff0`).
- 2026-10-30 — repository: Added `.gitattributes` and `.editorconfig`, finished `.gitignore` and made CI fetch full history (RW-19, `ca7b342`).
## v0.10.5 — 2026-10-29

- 2026-10-29 — build_gate: Fixed the kernel check failing a host unit of a `-g` build whose debug information names a `single_task` it only references; it reads the symbols the ELF64 or COFF object defines (`build_gate.py`).
- 2026-10-29 — sushi_packages: Fixed a nested package build recompiling the whole library whenever a package below it changed; a handed-down package reaches its flags through a stable link, not its digest folder (`package_resolver.py`).
