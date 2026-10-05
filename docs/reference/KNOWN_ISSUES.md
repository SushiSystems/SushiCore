# Known issues

Defects the estate audit of 2026-10-05 found that are still open. The audit is
`docs/agent/2026_10_05_ESTATE_AUDIT/REPORT.md`; the identifier in the last column is the finding
there, by section: Lic for Licence, Cli for Command line, Doc for Documentation, Lay for Layout
and hygiene, Code for Code shape. Work that is not a defect is in
[Remaining work](../design/REMAINING_WORK.md).

## Release state

| Issue | Where | Finding |
| --- | --- | --- |
| Versions 0.5.0, 0.6.0 and 0.7.0 were never tagged or published; PyPI carries 0.4.0 while seven CLIs require `sushicore>=0.7.0` | `pyproject.toml`, git tags | Lay L1 |
| Commits landed after the 0.7.0 release commit `c6d5f55` without a version change, so 0.7.0 names more than one tree | `pyproject.toml`, git history | Lay L4 |
| `release.yml` publishes on a tag without running the tests or the checkers | `.github/workflows/release.yml` | Lay L7 |
| `ci.yml` runs no checker | `.github/workflows/ci.yml` | Lay L6 |

## Machine output

| Issue | Where | Finding |
| --- | --- | --- |
| The `level` of a JSON `line` event is read from the icon prefix, so with the `emoji`, `minimal` or `none` icon set every warning and error is reported as `info` | `sushicore/renderer.py`, `_level_from_prefix` | Cli C3 |
| `doctor` puts Rich markup such as `[success]ok[/success]` in the rows of its `table` event | `sushicore/provision/doctor.py` | Cli C2 |
| A child process inherits stdout, so in machine mode stdout carries more than events | `sushicore/proc.py`, `Runner.run`; `sushicore/provision/steps.py`, `system.py`, `toolchains/oneapi.py` | Cli C4 |
| `setup`, `link` and `unlink` end without a `result` event | `sushicore/provision/commands.py` | Cli C5 |
| `config`, `env` and the executable picker build Rich tables and prompts directly, so they emit no `table` or `prompt` event | `sushicore/diag.py`, `sushicore/discovery.py` | Cli C6 |

## Commands

| Issue | Where | Finding |
| --- | --- | --- |
| A command run outside a checkout ends in `SystemExit(message)`: plain text on stderr, no console line | `sushicore/module_config.py`, `find_project_root` | Cli C8 |
| `link --workspace PATH` does not check the path for the workspace marker and creates `.sushistack/workspace.toml` there | `sushicore/provision/commands.py` | Cli C12 |
| `link` writes the module's pointer before the workspace's `[modules]` table and does not undo it when the second write fails | `sushicore/provision/commands.py` | Cli C12 |
| `doctor --for` does not list its groups in its help, and the groups `infer` and `eval` belong to one module | `sushicore/provision/commands.py`, `sushicore/provision/doctor.py` | Cli C16 |
| `--yes` has no `-y` form here and has one in `hub` | `sushicore/provision/commands.py` | Cli C17 |
| The `cli/` folder is fixed in the provisioning commands, and `InstallContext.program` defaults to `hub` | `sushicore/provision/commands.py`, `sushicore/provision/pipeline.py` | Cli C18 |
| `config` reports `config.toml` for a value that came from `config.local.toml` or from the linked workspace | `sushicore/diag.py`, `_source_of` | Cli C20 |
| `CMakeDriver.clean_tree` prints "removed" whether or not the tree is gone | `sushicore/cmake_driver.py` | CLI unification report, item 10 |
| An unknown `color` or `background` value falls back without a message, while an unknown `theme` or `icons` name is an error | `sushicore/config.py` | Cli C7 |

## Installing third-party software

| Issue | Where | Finding |
| --- | --- | --- |
| Downloaded archives and installers are extracted and run with no integrity check; only the Windows GPU installer download compares a digest, and that digest is MD5 | `sushicore/provision/packages/direct_download.py`, `github_release.py`, `sushicore/provision/toolchains/` | Code C6 |
| The oneAPI installer runs with `--eula accept`, and winget installs pass `--accept-package-agreements`, on the user's behalf | `sushicore/provision/toolchains/oneapi.py`, `sushicore/provision/packages/winget.py`, `sushicore/provision/steps.py`, `sushicore/provision/toolchains/adaptivecpp.py` | Lic L10 |
| The CUDA toolkit installs silently, which accepts NVIDIA's licence on the user's behalf | `sushicore/provision/gpu/cuda.py` | Lic L9 |
| Failures are swallowed by broad `except` clauses that return nothing and record nothing | `sushicore/provision/packages/base.py`, `direct_download.py`, `sushicore/provision/probe.py` | Code C5 |

## Source

| Issue | Where | Finding |
| --- | --- | --- |
| Two docstrings cite `docs/agent/specs/2026-09-05-hub-design.md`, a document of the SushiStack repository, as if it were here | `sushicore/renderer.py`, `sushicore/profile.py` | Cli C15 |
| A comment cites an absolute path on the owner's machine | `sushicore/theme.py` | Cli C19 |
| `workspace` and `config_base` import each other, hidden by imports inside functions | `sushicore/workspace.py`, `sushicore/config_base.py` | Code C4 |
| `_first_available` has no caller | `sushicore/provision/steps.py` | Code C24 |

## Documentation and layout

| Issue | Where | Finding |
| --- | --- | --- |
| The agent instruction file tells the reader to build with `se` and names folders this repository does not have; it moved to the root unchanged on 2026-10-05 | `AGENTS.md` | Doc D9, Lay L10, Lay L14 |
| An untracked plan sits in a folder the tree does not name, and a design document and a plan cite it, so the citation breaks in a clone | `docs/agent/plans/2026-09-25-hub-root-migration.md` | Lay L5, Doc D15 |
| That plan cites the provisioning design under its old path, `docs/agent/specs/2026-09-23-provision-design.md` | `docs/agent/plans/2026-09-25-hub-root-migration.md` | Doc D3 |
| The estate audit cites documents under the paths they had before the tree was built on 2026-10-05 | `docs/agent/2026_10_05_ESTATE_AUDIT/REPORT.md` | |
| Archived plans and reports carry absolute paths from one machine | `docs/archive/agent/plans/`, `docs/archive/agent/reports/` | Doc D14 |
| The standalone provisioning plan carries absolute paths from one machine, and none of its checkboxes was ticked as its tasks landed | `docs/agent/2026_10_04_STANDALONE_PROVISIONING/PLAN.md` | Doc D11, Doc D14 |
| The provisioning, module adoption and standalone provisioning work have no report | `docs/archive/agent/`, `docs/agent/2026_10_04_STANDALONE_PROVISIONING/` | Doc D10 |
| The archived entries of v0.1.0 to v0.3.0 are dated 2026-09-22, a day after those tags | `docs/archive/changelog/` | |
| No changelog entry records the 0.5.0, 0.6.0 and 0.7.0 version changes | `docs/reference/CHANGELOG.md` | Doc D7 |
| `tests/` mirrors the package tree, not the `unit`, `integration`, `regression`, `common` layout, and its golden files sit outside a `fixtures` folder | `tests/`, `tests/golden/` | Lay L13 |
| `pyproject.toml` sits in the repository root, where the layout rule forbids it | `pyproject.toml` | Lay L18 |
| The root has no `.gitattributes` and no `.editorconfig` | repository root | Lay L17 |
| `.gitignore` names neither `.pytest_cache/` nor `.superpowers/`; each is ignored only by a file the tool writes inside it | `.gitignore` | Lay L16 |
