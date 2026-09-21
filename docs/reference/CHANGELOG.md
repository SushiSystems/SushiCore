# Changelog

One line per meaningful change, newest first. Format: date, a past-tense verb, what changed, and
where, in backticks. No why; the reason lives in a design document the entry may link.

- 2026-09-21 — Added `help_group`, the Typer group that draws every help screen as a `HelpPage` (`sushicore/typer_help.py`).
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
