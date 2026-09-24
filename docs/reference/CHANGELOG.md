# Changelog

One line per meaningful change, newest first. Format: date, a past-tense verb, what changed, and
where, in backticks. No why; the reason lives in a design document the entry may link.

- 2026-09-24 — Made `doctor --for GROUP` count that group's optional checks as required, so their failures show FAIL and exit 1 (`sushicore/provision/doctor.py`).
- 2026-09-24 — workspace: Added a module-side link pointer that config loading follows to the linked workspace (`workspace.py`, `module_config.py`, `provision/commands.py`).
- 2026-09-23 — Renamed the shared package helpers to public names and made `setup` create a missing dependency root (`sushicore/provision/packages/`, `lock.py`).
- 2026-09-23 — Added `sushicore.provision`: dependency root, registry, doctor and module commands, moved from hub (`sushicore/provision/`).
- 2026-09-21 — Added `help_group`, the Typer group that draws every help screen as a `HelpPage` (`sushicore/typer_help.py`).
- 2026-09-22 — Stopped `typer_help` importing `click` at run time, since Typer 0.27 no longer installs it, and added `click` to the `test` extra (`sushicore/typer_help.py`, `pyproject.toml`).
- 2026-09-22 — Kept a bracket in a help title or list as text unless it names a style, so `[required]` and `[default: x]` show on Typer 0.27 (`sushicore/ui/definition_list.py`, `sushicore/ui/title.py`).
- 2026-09-22 — Added blank lines around the help logo and made definition-list terms not bold, so headings stand out (`sushicore/help/page.py`, `sushicore/ui/definition_list.py`).
- 2026-09-22 — Printed the help page on the console's Rich stream, not through Click's `echo`, which garbled true-colour codes on Windows (`sushicore/typer_help.py`).
- 2026-09-22 — Added `enable_virtual_terminal`, called when a `RichRenderer` is built, so a classic Windows console draws true colour (`sushicore/windows_console.py`, `sushicore/renderer.py`).
- 2026-09-21 — Kept a bracket in a table cell as text unless it names a style (`sushicore/markup.py`, `sushicore/ui/table.py`).
- 2026-09-21 — Added `group_by` to `Console.table` and coloured status words in tables (`sushicore/ui/table.py`, `sushicore/renderer.py`, `sushicore/console.py`).
- 2026-09-21 — Fixed `Logo.width` disagreeing with the drawn width when the wordmark rows differ in length (`sushicore/ui/logo.py`).
- 2026-09-21 — Made `help_group` fall back to Typer's own help, with one logged warning, when drawing the page fails (`sushicore/typer_help.py`).
- 2026-09-21 — Added `choose_logo` and replaced `HelpPage`'s `show_logo` with a `logo` field (`sushicore/help/logo_choice.py`, `sushicore/help/page.py`).
- 2026-09-21 — Added `is_dark_background`, the `[cli] background` setting and `Console.dark_background` (`sushicore/terminal_background.py`, `sushicore/config.py`, `sushicore/console.py`).
- 2026-09-21 — Added the wordmark, the white glow and `Logo.width`, and trimmed the mark's empty edge (`sushicore/brand.py`, `sushicore/ui/logo.py`).
- 2026-09-21 — Kept markup in `Header` and `Panel` titles and stopped `import sushicore` loading Rich (`sushicore/ui/header.py`, `sushicore/ui/panel.py`, `sushicore/renderer.py`).
- 2026-09-21 — Added `HelpPage`, which lays a help model out from components (`sushicore/help/page.py`).
- 2026-09-21 — Changed `RichRenderer.table`, `panel` and `header` to draw through components; tables lose their frame (`sushicore/renderer.py`).
- 2026-09-21 — Added `HelpModel` and `build_model`, which read a Click or Typer command into help data (`sushicore/help/model.py`, `sushicore/help/from_click.py`).
- 2026-09-21 — Added the `Title`, `Usage` and `DefinitionList` components (`sushicore/ui/`).
- 2026-09-21 — Added the `Header`, `Panel` and `Table` components (`sushicore/ui/`).
- 2026-09-21 — Added the `Logo` component (`sushicore/ui/logo.py`).
- 2026-09-21 — Added the maki logo as a palette and a pixel grid (`sushicore/brand.py`).
- 2026-09-21 — Added the `Component` protocol and the architecture test that guards `ui/` (`sushicore/ui/component.py`, `tests/test_ui_architecture.py`).
- 2026-09-21 — Added `Theme.muted` and `Console.theme` (`sushicore/theme.py`, `sushicore/console.py`).
- 2026-09-22 — Added `deps_fragment`, the one reader of a `sushistack.deps.toml` fragment (`sushicore/deps_fragment.py`).
- 2026-09-22 — Split `write_tool_section` into the document writer and its `[tool]`-merging caller (`sushicore/config_base.py`).
- 2026-09-22 — Moved the workspace contract into `workspace.py`: the marker, `workspace.toml` and the pre-2026-09-22 shared-config path (`sushicore/workspace.py`, `sushicore/module_config.py`).
- 2026-09-22 — Removed `WORKSPACE_CLI_DIR`, which named another repository's source layout (`sushicore/workspace.py`).
- 2026-09-22 — Kept sibling tables when writing `[tool]`, so one file can hold more than one section (`sushicore/config_base.py`).
- 2026-09-22 — Published 0.1.0 to PyPI from its own repository (`.github/workflows/release.yml`).
- 2026-09-22 — Split the package out of SushiStack with its own history (`git subtree split`).
