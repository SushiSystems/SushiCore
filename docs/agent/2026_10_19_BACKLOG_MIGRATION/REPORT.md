# Backlog migration: inventory

**Status:** Shipped — 2026-10-19. The owner approved the inventory as proposed.

The migration of this repository to the backlog format of SushiSkills'
`skills/documentation/BACKLOG_FORMAT.md`, step 2 of section 8 of SushiSkills'
`docs/agent/2026_10_19_BACKLOG_FORMAT/SPEC.md`. Every entry was read against the code and
`git log` on 2026-10-19. Where an entry is marked true without a measurement, no commit since
the entry was written (`037e316` for the known issues, `2921808` for the backlog) touched what
it names, or the code was read and still shows it.

## Shared tools

`copy_shared_tools.py` brought eleven files up to date and added `check_backlog.py`,
`design_status.py`, `check_probes.py`, `test_checker.py` and their tests. None held a local
edit. The new `check_layering.py` reads `K_PRIVATE_DEPENDS_ALSO`, which `tools/settings.py`
lacked; it was added with SushiSkills' default, `()`. `check_source_comments.py` now reports no
finding here.

## Backlog

Proposed IDs are in the last column. "Foreign" entries are closed by a commit in another
repository and leave this file.

### Decisions waiting for the owner

| Entry today | Verdict | Proposal |
| --- | --- | --- |
| Pushing `main`: 24 commits only on the owner's machine | Closed: `main` matches `origin/main` | Delete |
| Correcting `AGENTS.md` | True: line 41 still says `se build` | `RW-1` |
| The untracked hub root migration plan | Closed: committed as `docs/agent/2026_09_25_HUB_ROOT_MIGRATION/PLAN.md`. Two citations still use the old path | Delete; the citations become `RW-38` |
| A Python-library exception to the layout | True | `RW-2` |
| Python 3.10 kept while the floor is 3.11 | True: `ci.yml` tests 3.10 | `RW-3` |
| The provisioning reviews in `.superpowers/` | True; the same question as the documentation entry "a report after the fact" | `RW-4`, one entry for both |
| One policy for a bad appearance value | True | `RW-5` |
| Doctor groups through `ModuleProvision`, one spelling for `--yes` | True | `RW-6` |
| `K_SKIPPED_FOLDERS` gains `.superpowers` | Closed: the checkers skip what git ignores, and `.superpowers/` is ignored | Delete |
| Whether `gpu/windows_installer.py` is deleted (under GPU toolkit selection) | True: the file stays, nothing here calls it | `RW-7` |

### Open programmes

| Entry today | Verdict | Proposal |
| --- | --- | --- |
| Standalone wave 4: the owner runs each module's real `setup` and build | True | `RW-8`, unmeasured, Source `STANDALONE_PROVISIONING.md` |
| Standalone wave 4: the owner pushes each module repository | Foreign: the coordinating repository tracks the same programme | Delete |
| Documentation site: release the version with `docs_bundle` | Closed: released in 0.8.1 | Delete |
| Documentation site: each CLI's floor rises; `hub`, `st`, `se`, `sa`, `sb`, `sd` register `docs` | Foreign | Delete |
| Documentation site: this repository gets `docs/publish.toml` | Closed: the file exists | Delete |
| Provision phase B: the owner's real `hub migrate`, then `doctor`, build, finalize or rollback | True | `RW-9`, unmeasured, Source `PROVISION.md` |
| Provision phase B: rewrite the build caches and `cli/config.local.toml` to the new root | True: `migrate.py` does not touch them | `RW-10` |
| Provision phase B: the versioned layout `toolchains/<name>/<version>/` | True | `RW-11` |
| GPU toolkit: a real `sr` build against 13.x on an Ada or newer card | True | `RW-12`, unmeasured, Source `GPU_TOOLKIT_SELECTION.md` |
| GPU toolkit: a real `sr` build on the Pascal machine with 12.9.x | True | `RW-13`, unmeasured |
| GPU toolkit: the owner releases it; hub's and sushiruntime's floors follow | Closed for this repository: released in 0.9.0. The floors are foreign | Delete |
| GPU toolkit: a real ROCm install and `sr` build on Linux | True | `RW-14`, unmeasured |

### Deferred by the designs

| Entry today | Verdict | Proposal |
| --- | --- | --- |
| The build, test, package and deploy scaffold moves here | True | `RW-15` |
| `StackConfig.standalone_deps_dir` is removed | True: `stack_config.py` line 94 | `RW-16` |
| A binary command set for `se` | Foreign: `ModuleProvision.is_binary` is here; the command set is `se`'s | Delete |
| `setup` reads a module's `fragment` key | True: `pin_chain.py` uses `DEFAULT_FRAGMENT` | `RW-17` |
| The six CLIs adopt `help_group` | Foreign | Delete |
| Clone a Sushi library that only a fetched library pins | True | `RW-18` |

### Continuous integration

| Entry today | Verdict | Proposal |
| --- | --- | --- |
| A job that runs the checkers and the checker tests | Closed: `ci.yml` runs `tools/check_all.py` | Delete |
| The publish job depends on the tests and the checkers | Closed: `release.yml` needs the `ci` workflow | Delete |
| `.gitattributes`, `.editorconfig`, `.gitignore` entries | True | `RW-19` |

### Code programme

The measurement under the heading (65 source comment findings) is stale: the checker reports
none.

| Entry today | Verdict | Proposal |
| --- | --- | --- |
| Split `provision/steps.py` | True: 839 lines | `RW-20` |
| Move setup and doctor bodies out of `provision/commands.py` | True | `RW-21` |
| Declare a module's fragment path once | True: `StackConfig.fragment` and `ModuleProvision.fragment` | `RW-22` |
| Move `packages/base.run` below the package managers | True: `git_client.py` imports it | `RW-23` |
| Clone a Sushi library that only a fetched library pins | Listed twice; see `RW-18` | |
| Dispatch through the existing contracts (C2) | True | `RW-24` |
| Remove the consumers' names and commands (C3, Cli C18) | True: `"cli"` and `program = "hub"` | `RW-25` |
| One base error, no `SystemExit` (C7, Cli C8) | True: `module_config.py` line 69 | `RW-26` |
| One child-process brick (C8, Cli C4) | True: 41 direct `subprocess` calls, not 37 | `RW-27` |
| Merge the duplicated probe tables (C9) | True | `RW-28` |
| Keep Rich behind `Renderer` (C10, Cli C6) | True: `diag.py` builds `rich.table.Table` | `RW-29` |
| Replace the global console in `_output.py` (C11, Cli C3) | True: `console = _ConsoleProxy()` | `RW-30` |
| Shape the toolchain installers like the GPU backends (C12) | True | `RW-31` |
| Docstrings: 39 symbols without, 32 over eight lines (C13, C14, C21) | True; now 33 public symbols without and 37 over eight lines | `RW-32` |
| Split the other units with more than one responsibility (C15) | True | `RW-33` |
| Type the untyped seams on the build side (C16) | True | `RW-34` |
| Tests for `diag.py` and `typer_theme.py`; tests reaching into private names (C17, C19) | Stale: both test files exist; the private reach was not re-measured | `RW-35`, the private reach only |
| Hidden module state and class shape (C20, C22) | True | `RW-36` |
| One `result` event from every provisioning command (Cli C5) | True: no `result` in `commands.py` | `RW-37` |
| Validate the workspace before `link` writes (Cli C12) | True: `_resolve_workspace` returns `--workspace` unchecked | `RW-39` |

### Documentation

| Entry today | Verdict | Proposal |
| --- | --- | --- |
| One reference page for the shared command surface (Cli C11) | True | `RW-40` |
| A report written after the fact | Merged into `RW-4` | |
| Old paths cited in the sibling repositories | Foreign | Delete |
| (new) The old path of the hub root migration plan in `STANDALONE_PROVISIONING.md` line 15 and the standalone plan line 1369; the standalone plan's 43 absolute paths and 45 unticked boxes | True | `RW-38` |

## Known issues

| Issue today | Verdict | Proposal |
| --- | --- | --- |
| 0.5.0 and 0.6.0 never tagged or published | True | `KI-1`, `Fix: none, the versions were never published` |
| `release.yml` publishes without the tests | Closed | Delete |
| `ci.yml` runs no checker | Closed | Delete |
| JSON `line` level read from the icon prefix (Cli C3) | True: `_level_from_prefix` | `KI-2`, `Fix: RW-30` |
| `doctor` puts Rich markup in `table` rows (Cli C2) | True: `doctor.py` lines 94 to 96 | `KI-3`, `Fix: RW-41` (new) |
| A child inherits stdout in machine mode (Cli C4) | True | `KI-4`, `Fix: RW-27` |
| `setup`, `link`, `unlink` end without `result` (Cli C5) | True | `KI-5`, `Fix: RW-37` |
| `config`, `env`, the picker emit no `table` or `prompt` (Cli C6) | True | `KI-6`, `Fix: RW-29` |
| Outside a checkout, `SystemExit(message)` (Cli C8) | True | `KI-7`, `Fix: RW-26` |
| `link --workspace` creates a marker anywhere; `link` does not undo half a write (Cli C12) | True | `KI-8`, one entry, `Fix: RW-39` |
| `doctor --for` lists no groups; `infer` and `eval` belong to one module (Cli C16) | True | `KI-9`, `Fix: RW-6` |
| `--yes` has no `-y` here (Cli C17) | True | Merged into `KI-9` |
| `cli/` fixed, `program` defaults to `hub` (Cli C18) | True | `KI-10`, `Fix: RW-25` |
| `config` reports `config.toml` for a value from elsewhere (Cli C20) | True: `_source_of` | `KI-11`, `Fix: RW-42` (new) |
| `clean_tree` prints "removed" either way | True: `rmtree(..., ignore_errors=True)` | `KI-12`, `Fix: RW-43` (new) |
| An unknown `color` falls back in silence (Cli C7) | True | `KI-13`, `Fix: RW-5` |
| No fragment entry pins a `sha256` (Code C6) | True | `KI-14`, `Fix: RW-44` (new: pin a digest and a version for every download) |
| `git` and `doxygen` downloaded, declared nowhere (Code C6) | True | Merged into `KI-14` |
| Downloads take the newest release (Code C6) | True: `gh_latest_asset` | Merged into `KI-14` |
| Shell pipelines and clones unverified (Code C6) | True | `KI-15`, `Fix: RW-45` (new) |
| `--eula accept` and `--accept-package-agreements` on the user's behalf (Lic L10) | True | `KI-16`, `Fix: RW-46` (new decision: how a licence is shown and accepted) |
| ROCm tarballs unverified | True | `KI-17`, origin `dependency`, `Fix: none, AMD publishes no digest` |
| The CUDA toolkit unpacked without NVIDIA's licence shown (Lic L9) | True | Merged into `KI-16` |
| Broad `except` clauses that record nothing (Code C5) | Stale: `base.py` and `direct_download.py` now warn or log; `probe.py` line 83 still returns `None` silently | `KI-18`, `Where: probe.py`, `Fix: RW-47` (new) |
| Docstrings citing SushiStack's hub design (Cli C15) | Closed: no citation left | Delete |
| A comment with an absolute path in `theme.py` (Cli C19) | Closed | Delete |
| `workspace` and `config_base` import each other (Code C4) | True: lines 153 and 170 | `KI-19`, `Fix: RW-48` (new) |
| `_first_available` has no caller (Code C24) | True | `KI-20`, `Fix: RW-49` (new) |
| `AGENTS.md` names `se` and absent folders | True | `KI-21`, `Fix: RW-1` |
| An untracked plan in an unnamed folder | Closed: committed | Delete |
| That plan cites the provisioning design's old path | True, and as an absolute path | `KI-22`, `Fix: RW-38` |
| The estate audit cites old paths | True; a work folder records its time and is not the manual | Delete |
| Archived plans and reports carry absolute paths (Doc D14) | True: 25 files | `KI-23`, `Fix: none, the archive is frozen` |
| The standalone plan's absolute paths and unticked boxes | True | Merged into `KI-22` |
| No report for three pieces of work (Doc D10) | True | Delete; it is the decision `RW-4` |
| Archived v0.1.0 to v0.3.0 entries dated a day late | True | Merged into `KI-23` |
| No changelog entry for 0.5.0 to 0.7.0 | True | Merged into `KI-1` |
| `pyproject.toml` in the root (Lay L18) | True | `KI-24`, `Fix: RW-2` |
| No `.gitattributes`, `.editorconfig`; `.gitignore` gaps (Lay L16, L17) | True | `KI-25`, `Fix: RW-19` |

## Status lines

| File | Today | Proposal |
| --- | --- | --- |
| `docs/design/GPU_TOOLKIT_SELECTION.md` | "Built on 2026-10-14. CUDA ran end to end ..." | `Open — built and released in 0.9.0; the real builds of RW-12 to RW-14 are left` |
| `docs/agent/2026_09_25_HUB_ROOT_MIGRATION/PLAN.md` | none | `Open — tasks 5 and 6, the owner's real run` |
| `docs/agent/2026_10_04_STANDALONE_PROVISIONING/PLAN.md` | "Waves 1 to 3 landed ..." | `Open — wave 4, task 17` |
| `docs/agent/2026_10_05_CLI_UNIFICATION/SPEC.md` | "Shipped — seven CLIs adopted ..." | `Shipped — 2026-10-05. Seven CLIs adopted the surfaces; see REPORT.md.` |
| `docs/agent/2026_10_05_ESTATE_AUDIT/REPORT.md` | "Complete. ..." | `Shipped — 2026-10-05. Read-only audit.` |
| `docs/agent/2026_10_07_DOCS_BUNDLE/PLAN.md` (first file) | none; `SPEC.md` says Open | `Shipped — 2026-10-13. Released in 0.8.1.` |
| `docs/agent/2026_10_16_SUSHI_DEPENDENCY_RESOLUTION/PLAN.md` | none | `Shipped — 2026-10-17. Released in 0.9.1.` |

`PROVISION.md` and `STANDALONE_PROVISIONING.md` keep their `Open` lines and are cited by `RW-9`
and `RW-8`.

## Other files

| File | Finding | Proposal |
| --- | --- | --- |
| Roadmap, journal, handover, milestone or priority files | None | None |
| `README.md` | Has `## Status` since `5c7c0aa` | None |

## Outcome

The owner approved the inventory on 2026-10-19. The backlog holds `RW-1` to `RW-49`, eight of
them decisions and seven unmeasured; the known issues hold `KI-1` to `KI-25`. Seven status lines
took the four forms. `check_docs_truth.py` then found three history words and two cited paths
in the new entries, which were rewritten, and two allow-list entries that excused nothing,
which were deleted.

```
$ python tools/check_all.py .
clean: 11 checkers, tests
```
