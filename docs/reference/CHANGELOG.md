# Changelog

## Unreleased

- 2026-10-30 — provisioning: Reported each setup step once to a human and dropped the progress bar that repeated the progress line (RW-53, `388f822`).
- 2026-10-30 — command_line: Named the file a configuration value came from, the local file or the linked workspace (RW-42, `e31dd5a`).
- 2026-10-30 — provisioning: Resolved no vcpkg when a config turns use_vcpkg off, and kept the lookup for a config that never sets it (RW-51, `467b823`).
- 2026-10-30 — command_line: Accepted the short form of yes in setup, listed the check groups in the doctor help and let a module add its own groups (RW-6, KI-9, `a83e983`).
- 2026-10-30 — code: Broke the import cycle of the workspace and config modules by moving the TOML writer into its own module (RW-48, `24dcfff`).
- 2026-10-30 — code: Removed a helper in the provisioning steps that nothing called (RW-49, `c5844c3`).
- 2026-10-30 — config: Handled an unknown theme, icon set, colour or background the same way: it falls back to the default and the console prints one warning (RW-5, KI-13, `21eb93e`).
- 2026-10-30 — command_line: Let the console take a theme from extra config files, such as a workspace file (RW-52, `21eb93e`).
- 2026-10-30 — machine_output: Sent the table event as plain text, so a program no longer strips Rich tags from the doctor's cells (RW-41, KI-3, `a268415`).
- 2026-10-30 — command_line: Ended every provisioning command with one result event, through the outcome the commands return (RW-37, KI-5, `d63deb6`).
- 2026-10-30 — command_line: Made link refuse a path without the workspace marker and put the old link back when the registry write fails (RW-39, KI-8, `d63deb6`).
- 2026-10-30 — code: Moved the bodies of the four provisioning commands out of the module that registers them (RW-21, `d63deb6`).
- 2026-10-30 — downloads: Recorded why a failed probe found no Visual Studio instead of returning nothing in silence (RW-47, KI-18, `617a61d`).
- 2026-10-30 — commands: Reported a build tree that survived `clean` as a failure instead of as removed (RW-43, KI-12, `efb6ff0`).
- 2026-10-30 — repository: Added `.gitattributes` and `.editorconfig`, finished `.gitignore` and made CI fetch full history (RW-19, `ca7b342`).
## v0.10.5 — 2026-10-29

- 2026-10-29 — build_gate: Fixed the kernel check failing a host unit of a `-g` build whose debug information names a `single_task` it only references; it reads the symbols the ELF64 or COFF object defines (`build_gate.py`).
- 2026-10-29 — sushi_packages: Fixed a nested package build recompiling the whole library whenever a package below it changed; a handed-down package reaches its flags through a stable link, not its digest folder (`package_resolver.py`).
