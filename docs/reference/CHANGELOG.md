# Changelog

## Unreleased

## v0.9.6 — 2026-10-26

- 2026-10-26 — provision: Added `RunDirs`, `configure_arguments` and `search_path_variable`, what a consumer CLI takes from a resolved package set (`provision/sushi_packages/consumer_build.py`).
- 2026-10-26 — provision: Added `register_package_command`, the shared `package` command that installs a built tree to a prefix and archives it (`package_command.py`, `package_install.py`).
- 2026-10-26 — provision: Added `StackConfig.sushi_packages` and `package_keep`; `sushi_definitions` skips a packaged library (`stack_config.py`, `provision/config.py`).
- 2026-10-26 — provision: Added the package resolver, which builds each Sushi library once through its own CLI and reuses it from `<home>/packages` for every consumer (`provision/sushi_packages/`).
- 2026-10-26 — provision: Added `cli` and `package_exclude` to the `[module]` table of a dependency fragment (`deps_fragment.py`).
