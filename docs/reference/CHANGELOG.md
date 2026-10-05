# Changelog

## Unreleased

- 2026-10-05 — provision: Fixed the adapter build stopping with a TypeError when the probe found clang (`provision_adapters_for_run`, `sushicore/provision/steps.py`).
- 2026-10-05 — provision: Verified the archives and installers fetched by `download`, curl to a file or the GPU installer downloader against their pinned SHA-256 and stopped on a mismatch (`integrity.py`, `download_verifier.py`).
- 2026-10-05 — provision: Added the optional `sha256` key to a fragment entry (`sushicore/deps_fragment.py`, `sushicore/provision/fragments.py`, `docs/reference/DEPENDENCY_FRAGMENT.md`).
- 2026-10-05 — provision: Warned once per download with no pinned digest and listed them in doctor's `download digests` row (`DownloadVerifier`, `digest_check`).
- 2026-10-05 — sushicore: Logged the registry, cache, probe, os-release, cleanup and stream failures that were dropped and stopped catching defects with them (`sushicore/provision/`, `build_env.py`, `renderer.py`).
- 2026-10-05 — docs: Moved the design reasoning out of source comments and module docstrings into the manual (`docs/architecture/OVERVIEW.md`, `sushicore/provision/README.md`, `sushicore/`, `tests/`).
- 2026-10-05 — docs: Built the documentation tree, split the manual out of the two front doors, archived finished agent work and added the checkers (`docs/`, `tools/`, `README.md`, `sushicore/provision/README.md`).
- 2026-10-05 — cli: Documented that the entry point's reporter must look the console up when called (`entry.py`, `README.md`).
- 2026-10-05 — cli: Added the root options, diagnostic commands, alias table and entry point every Sushi CLI registers (`root_options.py`, `diag_commands.py`, `aliases.py`, `entry.py`, `describe.py`).
- 2026-10-05 — config: Raised ConfigError for a malformed TOML file and an unknown theme or icon set, where a decode error or ValueError escaped (`errors.py`, `read_toml`, `get_theme`).
- 2026-10-05 — licence: Replaced the Apache-2.0 licence with PolyForm Noncommercial 1.0.0, which ends free commercial use (`LICENSE`, `COMMERCIAL.md`, `NOTICE.md`, `README.md`).
- 2026-10-04 — provision: Added examples to the help of setup, doctor, link and unlink (`sushicore/provision/commands.py`).
- 2026-10-04 — provision: Built the GPU adapters against a toolchain already on the machine when the run installed none (`provision_adapters_for_run`).
- 2026-10-04 — provision: Made doctor pass a dependency a package manager holds when its check_cmd fails (`fragment_check`, `held_by_managers`).
- 2026-10-04 — provision: Reported a toolchain as not needed when another one provides its capability (`sushicore/provision/steps.py`).
- 2026-10-04 — config: Made StackConfig resolve the compiler and vcpkg across every dependency root and locate sibling checkouts (`sushicore/stack_config.py`, `sushicore/build_env.py`).
- 2026-10-04 — provision: Made setup follow depends_on, choose toolchains by the selection rule and take --toolchain and --no-gpu (`sushicore/provision/commands.py`).
- 2026-10-04 — provision: Added doctor checks for missing module checkouts and unsatisfied toolchain capabilities (`sushicore/provision/checks.py`).
- 2026-10-04 — provision: Added the dependency closure that follows a fragment's depends_on to each module's checkout (`sushicore/provision/closure.py`).
- 2026-10-04 — provision: Added the toolchain selection rule and its component table, moved from hub (`sushicore/provision/selection.py`).
- 2026-10-04 — provision: Added the shared base dependency fragment, moved from hub (`sushicore/provision/manifests/`).
- 2026-10-04 — provision: Made the probe find toolchains and vcpkg in every dependency root, the legacy trees included (`sushicore/provision/probe.py`).
- 2026-10-04 — provision: Recorded a module under its lower-cased key in fragments, the registry and a workspace's module list (`sushicore/profile.py`, `sushicore/provision/commands.py`).
- 2026-09-24 — proc: Added `Runner.capture` and the `catch_interrupt` and `missing_exit_code` options to `Runner` (`sushicore/proc.py`).
- 2026-09-24 — proc: Added `warn` to the `ConsoleLike` protocol (`sushicore/proc.py`).
- 2026-09-24 — cmake: Added the `jobs` and `config` options to `CMakeDriver` (`sushicore/cmake_driver.py`).
- 2026-09-24 — build_env: Added `build_env.snapshot_vcvars` and `provision.probe.find_vcvars` (`sushicore/build_env.py`, `sushicore/provision/probe.py`).
- 2026-09-24 — provision: Added `InstallContext.program` and named the calling program in install hints (`sushicore/provision/pipeline.py`).
- 2026-09-24 — doctor: Made `doctor --for GROUP` count that group's optional checks as required (`sushicore/provision/doctor.py`).
- 2026-09-24 — workspace: Added a module-side link pointer that config loading follows to the linked workspace (`sushicore/workspace.py`, `sushicore/module_config.py`, `sushicore/provision/commands.py`).
- 2026-09-23 — provision: Renamed the shared package helpers to public names and made `setup` create a missing dependency root (`sushicore/provision/packages/`, `sushicore/provision/lock.py`).
- 2026-09-23 — provision: Added `sushicore.provision`: dependency root, registry, doctor and module commands, moved from hub (`sushicore/provision/`).

## v0.4.0 — 2026-09-22

- 2026-09-22 — help: Stopped typer_help importing click at run time and added click to the `test` extra (`sushicore/typer_help.py`, `pyproject.toml`).
- 2026-09-22 — ui: Kept a bracket in a help title or list as text unless it names a style (`sushicore/ui/definition_list.py`, `sushicore/ui/title.py`).
- 2026-09-22 — help: Added blank lines around the help logo and made definition-list terms not bold (`sushicore/help/page.py`, `sushicore/ui/definition_list.py`).
- 2026-09-22 — help: Printed the help page on the console's Rich stream, not through Click's `echo` (`sushicore/typer_help.py`).
- 2026-09-22 — renderer: Added `enable_virtual_terminal`, called when a `RichRenderer` is built, so a classic Windows console draws true colour (`sushicore/windows_console.py`, `sushicore/renderer.py`).
- 2026-09-21 — help: Added `help_group`, the Typer group that draws every help screen as a `HelpPage` (`sushicore/typer_help.py`).
- 2026-09-21 — ui: Kept a bracket in a table cell as text unless it names a style (`sushicore/markup.py`, `sushicore/ui/table.py`).
- 2026-09-21 — ui: Added `group_by` to `Console.table` and coloured status words in tables (`sushicore/ui/table.py`, `sushicore/renderer.py`, `sushicore/console.py`).
- 2026-09-21 — ui: Fixed `Logo.width` disagreeing with the drawn width when the wordmark rows differ in length (`sushicore/ui/logo.py`).
- 2026-09-21 — help: Made `help_group` fall back to Typer's own help, with one logged warning, when drawing the page fails (`sushicore/typer_help.py`).
- 2026-09-21 — help: Added `choose_logo`, which picks the logo a console is wide enough for (`sushicore/help/logo_choice.py`).
- 2026-09-21 — help: Replaced `HelpPage`'s `show_logo` with a `logo` field (`sushicore/help/page.py`).
- 2026-09-21 — config: Added `is_dark_background` and the `[cli] background` setting (`sushicore/terminal_background.py`, `sushicore/config.py`).
- 2026-09-21 — console: Added `Console.dark_background` (`sushicore/console.py`).
- 2026-09-21 — ui: Added the wordmark, the white glow and `Logo.width`, and trimmed the mark's empty edge (`sushicore/brand.py`, `sushicore/ui/logo.py`).
- 2026-09-21 — ui: Kept markup in `Header` and `Panel` titles (`sushicore/ui/header.py`, `sushicore/ui/panel.py`).
- 2026-09-21 — renderer: Stopped `import sushicore` loading Rich (`sushicore/renderer.py`).
- 2026-09-21 — help: Added `HelpPage`, which lays a help model out from components (`sushicore/help/page.py`).
- 2026-09-21 — renderer: Changed `RichRenderer.table`, `panel` and `header` to draw through components; tables lose their frame (`sushicore/renderer.py`).
- 2026-09-21 — help: Added `HelpModel` and `build_model`, which read a Click or Typer command into help data (`sushicore/help/model.py`, `sushicore/help/from_click.py`).
- 2026-09-21 — ui: Added the `Title`, `Usage` and `DefinitionList` components (`sushicore/ui/`).
- 2026-09-21 — ui: Added the `Header`, `Panel` and `Table` components (`sushicore/ui/`).
- 2026-09-21 — ui: Added the `Logo` component (`sushicore/ui/logo.py`).
- 2026-09-21 — brand: Added the maki logo as a palette and a pixel grid (`sushicore/brand.py`).
- 2026-09-21 — ui: Added the `Component` protocol and the architecture test that guards `ui/` (`sushicore/ui/component.py`, `tests/test_ui_architecture.py`).
- 2026-09-21 — theme: Added `Theme.muted` and `Console.theme` (`sushicore/theme.py`, `sushicore/console.py`).
