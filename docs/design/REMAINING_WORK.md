# Remaining work

The single backlog of this repository. Defects are in
[Known issues](../reference/KNOWN_ISSUES.md); this page holds work and decisions. Finding
identifiers refer to `docs/agent/2026_10_05_ESTATE_AUDIT/REPORT.md`, by section: Lic, Cli, Doc,
Lay, Code.

## Open programmes

### Standalone provisioning, wave 4

Design: [Standalone provisioning](STANDALONE_PROVISIONING.md). Plan:
`docs/agent/2026_10_04_STANDALONE_PROVISIONING/PLAN.md`, Task 17. Waves 1 to 3 landed on
2026-10-04 in this repository, the six module CLIs and hub. The SushiStack repository tracks the
same programme in its own `docs/design/REMAINING_WORK.md`.

- The owner runs the real `setup` and build of `sr`, `sb`, `sa`, `sd`, `st`, and `se` last.
- The owner pushes each module repository. sushicore 0.7.0 was tagged on 2026-10-05.

### Provision, phase B

Design: [Provision](PROVISION.md), "Phase B: hub's tree moves". Hub's dependency tree moves from
`<workspace>/dependencies` to a directory the owner names, with a junction left at the old path.
Its plan is `docs/agent/plans/2026-09-25-hub-root-migration.md`, which is untracked. Tasks 1 to
4 of that plan exist in sushicore 0.8.0 and in hub: `sushicore/provision/links.py`,
`migrate.py`, `user_environment.py` and `hub migrate`. What is left:

- The owner's real run of `hub migrate`, then each module's `doctor` and build, then
  `hub migrate --finalize` or `--rollback` (plan Tasks 5 and 6).
- Rewriting the build caches and each module's `cli/config.local.toml` to the new root. Until
  then the link at the old path has to stay.
- The versioned layout `toolchains/<name>/<version>/`.

## Deferred by the designs

- The build, test, package and deploy scaffold that `sushiai` and `sushiblas` each carry in
  `cli/.../services/project.py` moves here (Provision, "Sub-projects").
- `StackConfig.standalone_deps_dir` is removed one release after its last override is gone.
- A binary command set for `se`; the registration is ready for it through
  `ModuleProvision.is_binary`.
- `setup` reads a dependency module's `fragment` key from its `sushi-module.toml`. Every module
  uses the default path today.
- `sr`, `se`, `sa`, `sb`, `sd` and `st` adopt `help_group` on their own schedule; whether all six
  have was not checked here.

## Decisions waiting for the owner

- Pushing `main`: 24 commits exist only on the owner's machine as of 2026-10-05 (Lay L2).
- Correcting the stale lines of `AGENTS.md`, which moved from `docs/CLAUDE.md` as it was, and
  naming the skills this repository follows in it (Doc D9, Lay L10, Lay L14).
- The untracked hub root migration plan: commit it as
  `docs/agent/2026_09_25_HUB_ROOT_MIGRATION/PLAN.md`, or move it to the SushiStack repository,
  whose work it plans (Lay L5, Doc D15).
- A Python-library exception to the repository layout, or a move to it: `pyproject.toml` in the
  root, a flat package, and `tests/` mirroring the package (Lay L13, Lay L18).
- Python 3.10 stays supported while the Python style rule sets 3.11 as the floor (Code C18). The
  checkers under `tools/` already need 3.11.
- The review reports of the provisioning work sit untracked in `.superpowers/`; whether one
  tracked report is written from them or they are discarded (Doc D10, Lay L15).
- One policy for a bad appearance value: an unknown `theme` fails, an unknown `color` falls back
  in silence (Cli C7).
- Whether a module contributes its doctor groups through `ModuleProvision`, and one spelling for
  `--yes` across the shared commands and hub (Cli C16, Cli C17).
- Whether `K_SKIPPED_FOLDERS` in `tools/documentation/check_source_comments.py` gains
  `.superpowers`; the checker reads the four probe scripts there and reports them.

## Continuous integration

Workflow files change after the code programme, when the source comment checker can pass.

- Add a job that runs the checkers and `python -m unittest discover -s tools/tests` (Lay L6).
- Make the publish job depend on the test matrix and the checkers (Lay L7).
- Add `.gitattributes` and `.editorconfig`, and name `.pytest_cache/` and `.superpowers/` in
  `.gitignore` (Lay L16, Lay L17).

## Code programme

Programme 5 of the estate refactor. Measured on 2026-10-05,
`python tools/documentation/check_source_comments.py .` reports 65 findings: 21 file headers, 25
runs of stacked comment lines, 15 separator lines, and 4 license blocks in the untracked probe
scripts under `.superpowers/`.

- Split `provision/steps.py`, which holds four step classes in about 820 lines (Code C1).
- Dispatch on platform and package manager through the existing contracts where the code now
  switches on a name (Code C2).
- Remove the consumers' names and commands from the shared code (Code C3, Cli C18).
- Give the package one base error and stop signalling failure by `bool`, `None` and bare
  built-in exceptions; raise it where `find_project_root` raises `SystemExit` (Code C7, Cli C8).
- One child-process brick in place of four runner copies and 37 direct `subprocess` calls; it
  also keeps stdout to events in machine mode (Code C8, Cli C4).
- Merge the duplicated probe tables and helpers in `provision` (Code C9).
- Keep Rich behind the `Renderer` seam: `Console.console`, `diag.py`, `discovery.py` and ten call
  sites in `provision` reach past it (Code C10, Cli C6).
- Replace the global console in `provision/_output.py` and carry the level through
  `Renderer.line` (Code C11, Cli C3).
- Shape the toolchain installers like the GPU backends (Code C12).
- Bring file openings and docstrings to the source comment rule: 39 symbols have no docstring
  and 32 docstrings exceed eight lines (Code C13, Code C14, Code C21).
- Split the units with more than one responsibility outside `steps.py` (Code C15).
- Type the untyped seams on the build side (Code C16).
- Add tests for `diag.py` and `typer_theme.py`, and stop tests reaching into private names
  (Code C17, Code C19).
- Remove hidden module state (Code C20) and apply the class-shape rules outside `ui` and `help`
  (Code C22).
- Emit one `result` event from every provisioning command through one exit helper (Cli C5).
- Validate the workspace before `link` writes, and make its two edits one operation (Cli C12).

## Documentation

- One reference page for the shared command surface: commands, options and exit codes of every
  registered command (Cli C11). The provisioning commands are covered in
  `sushicore/provision/README.md`; `config`, `env`, `--version` and `--describe` are not.
- A report for the provisioning, module adoption and standalone provisioning work, if the owner
  wants one written after the fact (Doc D10).
- Citations of this repository's old document paths in the SushiStack repository and in the
  sibling CLIs were not searched; `docs/agent/specs/2026-10-04-standalone-provision-design.md`
  is cited in SushiStack's `docs/design/REMAINING_WORK.md`.
