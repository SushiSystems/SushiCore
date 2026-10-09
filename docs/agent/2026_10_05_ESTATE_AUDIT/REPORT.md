# Estate audit: sushicore

**Status:** Complete. Read-only audit of 2026-10-05; nothing in the repository was changed.

One auditing agent per dimension read the tree and a second agent checked each finding against
the files. A finding marked *confirmed* was re-read by the reviewer; *unclear* means the reviewer
could not settle it; *found by review* means the first pass missed it and nobody re-checked it.
Refuted findings are listed and not counted. No build, test or project CLI was run.

| Dimension | High | Medium | Low | Refuted |
| --- | --- | --- | --- | --- |
| Licence | 3 | 8 | 5 | 0 |
| Command line | 4 | 9 | 8 | 0 |
| Documentation | 5 | 11 | 2 | 0 |
| Layout and hygiene | 4 | 10 | 6 | 0 |
| Code shape | 6 | 14 | 4 | 0 |

## Licence

### Facts

- Tree: 212 tracked files at HEAD 9597b64 (164 .py, 39 .md, 2 .yml, 2 .toml, 2 golden .txt, py.typed, LICENSE, .gitignore). Pure Python; no C++, GLSL, TypeScript, CMake, Doxyfile, Dockerfile, package.json, conda file or sushi-module.toml is tracked.
- D:/Projects/sushicore/LICENSE is the unmodified Apache License 2.0 text, 201 lines. Its appendix still reads 'Copyright [yyyy] [name of copyright owner]' (line 189), so the file names no holder.
- No other licence document is tracked: no NOTICE, COPYING, docs/LICENSE, AUTHORS, CITATION or third_party/ folder. The only other copy is the ignored build output sushicore.egg-info/.
- Header variant A, the only one in the tree, sits on lines 1-2 of 82 .py files: '# Copyright (c) 2026-present Mustafa Garip & Sushi Systems' / '# Licensed under the Apache License, Version 2.0. See LICENSE.'
- Variant A by area: 42 files in sushicore/provision/** (all of that package), 37 in tests/provision/, 3 in tests/ root. Examples: sushicore/provision/doctor.py, tests/provision/test_manifests.py, tests/test_stack_config.py.
- No header at all: 82 .py files. Package: 27 in sushicore/ root, 9 in sushicore/ui/, 5 in sushicore/help/ (41). Tests: 25 in tests/ root, 10 in tests/ui/, 5 in tests/help/, 1 tests/provision/__init__.py (41). Examples: sushicore/__init__.py, sushicore/cmake_driver.py, sushicore/console.py.
- No file carries an SPDX-License-Identifier line, and no .py file carries any copyright or licence string other than variant A.
- Non-Python files carry no header: pyproject.toml, sushicore/provision/manifests/base.deps.toml, .github/workflows/ci.yml, .github/workflows/release.yml, tests/golden/logo_*_truecolor.txt.
- Machine-readable declaration, pyproject.toml lines 10-11: license = "Apache-2.0", license-files = ["LICENSE"]. Classifiers (lines 12-19) hold no licence classifier. Build backend setuptools>=77.0 validates the SPDX expression.
- pyproject.toml line 20 names the author as Mustafa Garip <mustafagarip@sushisystems.io>; project URLs point to https://github.com/SushiSystems/SushiCore. Version on HEAD is 0.7.0.
- Prose statements in tracked manual pages: README.md line 84 'Licensed under the terms in `LICENSE`.' (licence-neutral wording). docs/README.md and docs/CLAUDE.md say nothing about the licence.
- docs/agent/plans/ quote the Apache header inside code samples: 2026-09-23-provision.md (22 lines), 2026-09-24-module-adoption.md (9), 2026-10-04-standalone-provision.md (7).
- Copyright holder and year: one form only, 'Mustafa Garip & Sushi Systems', '2026-present'. First commit is dated 2026-08-25.
- git shortlog -sne HEAD: one author, 129 commits, Mustafa Garip <mustafa.garip3434@hotmail.com>; the committer is the same identity on all 129. No other human author.
- Commit trailers name AI co-authors only: 116 'Co-Authored-By: Claude ...' lines (Opus 5.5 1M 47, Sonnet 5 24, Opus 5.5 18, Opus 5 1M 18, Fable 5.1 9), all noreply@anthropic.com.
- Tags v0.1.0, v0.2.0, v0.3.0, v0.4.0 exist locally and on origin (git ls-remote). Each tagged tree holds LICENSE and license = "Apache-2.0". HEAD is 18 commits ahead of origin/main.
- docs/reference/CHANGELOG.md line 55: '2026-09-22 — Published 0.1.0 to PyPI from its own repository'. .github/workflows/release.yml publishes to PyPI on every pushed v* tag through pypa/gh-action-pypi-publish.
- Runtime pip dependencies (pyproject.toml lines 22-25, 31-33): rich>=13.0, tomli>=2.0 on Python < 3.11; extras typer>=0.12, pytest>=7.0, click>=8.0; build-time setuptools>=77.0. None is vendored and no notice for them is kept in the repo. Imports seen: rich 48, pytest 32, typer 9, click 2.
- Licences of those packages from memory, not read from their sources in this pass: rich MIT, typer MIT, tomli MIT, pytest MIT, setuptools MIT, click BSD-3-Clause.
- No code is vendored and nothing is fetched at build time. sushicore/provision installs tools on the user's machine at run time: apt packages and vcpkg ports listed in sushicore/provision/manifests/base.deps.toml (build-essential, cmake, ninja, gtest, opencl, pkgconf), winget packages, direct GitHub release downloads.
- Run-time provisioning also reaches proprietary and separately licensed software: NVIDIA CUDA 12.6.3 installer (sushicore/provision/gpu/cuda.py lines 39-49), a clone of https://github.com/intel/llvm.git (sushicore/provision/gpu/adapter_builder.py line 32), and a oneapi_root setting (sushicore/provision/config.py line 25).
- Ignored and untracked: sushicore.egg-info/PKG-INFO says 'License-Expression: Apache-2.0', Version 0.7.0; .superpowers/sdd/ briefs repeat the Apache header many times. Neither is in git.

### Corrections from review

- F11 title 'All commits list an AI co-author' is wrong: 116 trailers across 129 commits, so at least 13 commits carry none. The body's figure of 116 is correct.
- Fact 'Run-time provisioning also reaches proprietary software ... a oneapi_root setting (config.py line 25)' understates it: sushicore/provision/toolchains/oneapi.py:19-23 downloads Intel's offline oneAPI installer and lines 80 and 101 run it with '--eula accept'. The repo also adds Intel's and AMD's apt repositories (sushicore/provision/system.py:20,63; sushicore/provision/gpu/rocm.py:44-47).
- F12 and the fact 'HEAD is 18 commits ahead of origin/main' leave the pushed version open. Corrected: origin/main (9c0fce1) has version = "0.6.0", so 0.5.0 (a5fa5ae) and 0.6.0 are public on GitHub under Apache-2.0 without tags; only 0.7.0 (c6d5f55) is unpushed.
- docs/agent/plans/2026-09-24-module-adoption.md mentions Apache on 11 lines, not 9; the 9 counts only the quoted header line. Lines 18 and 588 are prose ('st files touched get the Apache header', '`LICENSE` is Apache-2.0').
- Recomputed and correct: 212 tracked files, 164 .py, 82 with header / 82 without and the per-folder split; one author with 129 commits; four tags, each Apache-2.0 with LICENSE; LICENSE 201 lines with the template on line 189.

### Findings

#### L1. [high] Four tagged versions and at least one PyPI release are already out under Apache-2.0 and cannot be retracted

Evidence: git ls-remote --tags origin lists v0.1.0, v0.2.0, v0.3.0, v0.4.0 on https://github.com/SushiSystems/SushiCore.git; each tagged pyproject.toml reads license = "Apache-2.0" and each tree holds LICENSE. D:/Projects/sushicore/docs/reference/CHANGELOG.md:55 records 'Published 0.1.0 to PyPI'. D:/Projects/sushicore/.github/workflows/release.yml:3-5 and :38 publish on every pushed v* tag, so v0.2.0-v0.4.0 probably reached PyPI as well; I did not query PyPI.

Recommendation: Treat everything up to the last Apache-tagged commit as permanently Apache-2.0: anyone, companies included, may keep using and forking those versions. Apply the new licence from one named version onward, state that cut in the changelog and README, and check pypi.org/project/sushicore to list exactly which versions are public.

Review: confirmed. git ls-remote --tags origin returns v0.1.0-v0.4.0; each tagged pyproject.toml reads license = "Apache-2.0" and each tree holds LICENSE; CHANGELOG.md:55 and release.yml:3-5,38 read as cited. Understated: origin/main also carries 0.5.0 and 0.6.0 untagged (see missed).

#### L2. [high] Half of the Python files carry no licence header

Evidence: 82 of 164 tracked .py files have no header. Package: 27 in sushicore/ root (sushicore/__init__.py, sushicore/cmake_driver.py, sushicore/console.py), 9 in sushicore/ui/, 5 in sushicore/help/. Tests: 25 in tests/ root, 10 in tests/ui/, 5 in tests/help/, and tests/provision/__init__.py. Only sushicore/provision/** (42) and 40 test files have one. The source-comments skill requires every file to open with the licence block.

Recommendation: The relicence pass has to add a header to these 82 files, not only replace the existing 82. Write the header once as a template and apply it to all 164, so that one checker rule (tools/documentation/check_source_comments.py, absent in this repo) can hold it.

Review: confirmed. Recomputed over git ls-files '*.py': 82 without header (27 sushicore/, 9 ui, 5 help, 25 tests/, 10 tests/ui, 5 tests/help, 1 tests/provision). source-comments requires the licence block on every file. No tools/ folder exists, as stated.

#### L3. [high] Versions 0.5.0 and 0.6.0 are already public under Apache-2.0 on origin/main, so the earliest clean cut is 0.7.0

Evidence: git show origin/main:pyproject.toml gives version = "0.6.0" with license = "Apache-2.0"; git log -- pyproject.toml shows a5fa5ae 'chore(release): prepare sushicore 0.5.0' (2026-09-23) behind origin/main and c6d5f55 'prepare sushicore 0.7.0' (2026-10-04) among the 18 unpushed commits. The audit's F1 limits the Apache grant to the four tags and F12 leaves the question open.

Recommendation: State the Apache boundary as origin/main at 9c0fce1 (0.6.0), not v0.4.0. The 18 local commits, 0.7.0 included, are the only code nobody has received; change LICENSE, pyproject and the headers before they are pushed, so 0.7.0 is the first version under the new licence.

Review: found by review.

#### L4. [medium] 82 files name Apache-2.0 in their header and all need rewriting

Evidence: '# Licensed under the Apache License, Version 2.0. See LICENSE.' on line 2 of 82 files: 42 under sushicore/provision/, 37 under tests/provision/, plus tests/test_stack_config.py, tests/test_workspace_link.py, tests/test_workspace_modules.py.

Recommendation: Replace line 2 in all 82 with the new licence name, or better an 'SPDX-License-Identifier:' line that a script can check. Keep the copyright line decision (F5) in the same pass.

Review: confirmed. 82 files carry the two-line Apache header: 42 under sushicore/provision (17+10+1+8+6), 37 tests/provision, 3 tests/ root. Copyright is on line 1 in all 82.

#### L5. [medium] The header does not have the shape the source-comments rule prescribes

Evidence: Existing header is two '#' lines (D:/Projects/sushicore/sushicore/provision/doctor.py:1-2). C:/Users/sushi/.claude/skills/source-comments/SKILL.md shows a block whose first line is the file name, followed by project name, repository URL, organisation site, copyright and the licence notice, then a blank line before the docstring. Here the docstring follows on line 3 with no blank line, and no file name, project or URL appears.

Recommendation: Decide the canonical Python header once for all Sushi repositories before the relicence pass, since every file is touched anyway. The skill's example is C++ and quotes an 'Apache-2.0 notice'; it needs a Python form and the new licence text.

Review: confirmed. Header is two '#' lines with the docstring on line 3; the skill's block opens with the file name, project, URLs, copyright and notice, then a blank line. The skill gives no Python form, so the 'decide once' recommendation is right.

#### L6. [medium] Copyright holder is a person and an organisation joined by '&', with no statement of who owns what

Evidence: 'Copyright (c) 2026-present Mustafa Garip & Sushi Systems' in 82 files. LICENSE line 189 is the unfilled template 'Copyright [yyyy] [name of copyright owner]', so the root names no holder. pyproject.toml:20 lists only Mustafa Garip as author. No document in the repo says whether Sushi Systems is a registered legal entity.

Recommendation: Owner decision: one holder (the person, or the company if it exists as a legal entity) or a deliberate joint statement. A non-commercial licence is enforced by its holder, and a commercial exception can only be granted by whoever that is, so the name has to be unambiguous. Put the same line in LICENSE, the headers and pyproject.

Review: confirmed. LICENSE:189 is the unfilled Apache appendix template; the 82 headers name 'Mustafa Garip & Sushi Systems'; pyproject.toml:20 names only the person. An unfilled appendix is normal for Apache, the ambiguity of the joint holder is the real point.

#### L7. [medium] pyproject licence fields must change together and need a valid SPDX expression

Evidence: D:/Projects/sushicore/pyproject.toml:10-11: license = "Apache-2.0", license-files = ["LICENSE"]; build backend setuptools>=77.0 (line 2) rejects strings that are not SPDX expressions. The ignored sushicore.egg-info/PKG-INFO carries 'License-Expression: Apache-2.0' and will go stale.

Recommendation: If the owner picks a licence on the SPDX list (PolyForm-Noncommercial-1.0.0 is on it) use that id; a custom text needs 'LicenseRef-<name>'. Do not add an 'OSI Approved' classifier: a non-commercial licence is not open source by the OSI definition, and PyPI text and README should say 'source-available'.

Review: confirmed. pyproject.toml:2,10-11 as cited; no licence classifier in lines 12-19. PolyForm-Noncommercial-1.0.0 is an SPDX id. egg-info is ignored (.gitignore), so its staleness is a non-issue rather than a defect.

#### L8. [medium] The organisation's own dependency rule rejects non-commercial licences, and every sibling repository depends on sushicore

Evidence: C:/Users/sushi/.claude/skills/dependencies/SKILL.md licence table: 'Non-commercial, source-available, field-of-use limits | Rejected'. D:/Projects/sushicore/pyproject.toml:8 describes sushicore as the shared core of hub, sr, se, sa, sb, sd, st.

Recommendation: Amend the dependencies skill in the same programme so that first-party Sushi Systems packages under the new licence are accepted, while third-party non-commercial code stays rejected. Otherwise the rule and the repositories contradict each other on the day of the change.

Review: confirmed. dependencies skill table has the row 'Non-commercial, source-available, field-of-use limits | Rejected'; pyproject.toml:8 names hub/sr/se/sa/sb/sd/st. The fix is one exception row in one skill, brick-shaped.

#### L9. [medium] The CUDA installer is run silently, which accepts NVIDIA's EULA on the user's behalf

Evidence: D:/Projects/sushicore/sushicore/provision/gpu/cuda.py:39-49 downloads cuda_12.6.3_windows_network.exe from developer.download.nvidia.com and passes '-s' with component names. Lines 104 onward install the toolkit from NVIDIA's apt repository. sushicore/provision/config.py:25 also handles a oneAPI root. Both are proprietary SDKs under vendor EULAs; nothing in README.md or docs/ tells the user that.

Recommendation: Nothing here is redistributed, so the outbound licence is not blocked. Still, add a third-party notice page that lists every tool the provisioner installs with its licence and vendor terms, and have the CUDA step say that it installs under NVIDIA's EULA. The dependencies skill rejects vendor SDK licences for linked dependencies; record that these are user-installed tools, not dependencies.

Review: confirmed. cuda.py:39-49 read as cited ('-s' silent network installer); apt path starts at line 103. Evidence is too narrow: the oneAPI reference should be toolchains/oneapi.py:80 and :101, which pass '--eula accept' explicitly, not config.py:25 (see missed).

#### L10. [medium] The oneAPI installer is run with an explicit '--eula accept', and winget installs pass '--accept-package-agreements'

Evidence: D:/Projects/sushicore/sushicore/provision/toolchains/oneapi.py:80 and :101 pass '-s','-a','--silent','--eula','accept' to Intel's offline installer downloaded from the URL at lines 19-23. D:/Projects/sushicore/sushicore/provision/packages/winget.py:39, sushicore/provision/steps.py:609 and sushicore/provision/toolchains/adaptivecpp.py:315 pass '--accept-package-agreements --accept-source-agreements'. F8 cites only cuda.py and config.py:25.

Recommendation: Widen F8 to these call sites. One consent brick in sushicore/provision (a single function that names the vendor terms and records the user's yes) that every installer step calls, rather than a notice added to each step; the third-party notice page lists the same vendors.

Review: found by review.

#### L11. [medium] No inbound contribution terms exist, so a future outside contribution would block the owner from granting commercial exceptions

Evidence: git ls-files docs shows no docs/CONTRIBUTING.md (only docs/CLAUDE.md, docs/README.md, docs/agent/**, docs/reference/CHANGELOG.md); no CLA or DCO text anywhere in the tree. Today the single author makes relicensing possible (git shortlog: one identity, 129 commits).

Recommendation: When the licence changes, add docs/CONTRIBUTING.md with a contributor agreement that assigns or licenses contributions to the named holder, so the holder keeps the right to sell commercial licences. It depends on the F5 holder decision.

Review: found by review.

#### L12. [low] No third-party notice exists for the pip dependencies

Evidence: pyproject.toml:22-25 and 31-33 declare rich, tomli, typer, pytest, click; build uses setuptools. No NOTICE, THIRD_PARTY or docs/reference page is tracked (git ls-files shows only LICENSE). All are permissive (MIT, BSD-3-Clause as far as I recall) and none is vendored, so no notice is legally required and none conflicts with a non-commercial outbound licence. No GPL or LGPL dependency was found.

Recommendation: Add a short docs/reference/THIRD_PARTY.md with name, version floor, licence read from each package's own metadata, and whether it is runtime, extra or build. It makes the 'no copyleft' claim checkable when the licence changes.

Review: confirmed. pyproject.toml:22-25, 31-33 as cited; git ls-files shows LICENSE as the only licence document. Licences are from the auditor's memory, which the dependencies skill forbids ('read it'); the audit admits this under not_checked.

#### L13. [low] Author e-mail differs between git history and package metadata

Evidence: git shortlog -sne: Mustafa Garip <mustafa.garip3434@hotmail.com>, 129 commits. pyproject.toml:20: mustafagarip@sushisystems.io. One person, two identities.

Recommendation: Not a relicensing obstacle, since the sole author can relicense his own work. Record in the licence decision document that both addresses are the same person, so a later reader of the history does not count two contributors.

Review: confirmed. git shortlog -sne HEAD: 129 commits, mustafa.garip3434@hotmail.com; pyproject.toml:20: mustafagarip@sushisystems.io.

#### L14. [low] All commits list an AI co-author

Evidence: 116 'Co-Authored-By: Claude ... <noreply@anthropic.com>' trailers across 129 commits (git log --format=%B). No human contributor besides the owner.

Recommendation: No consent from another person is needed for the change. The trailers do not create a second copyright holder under Anthropic's terms as I understand them, but that is a legal reading I have not verified; if the owner takes legal advice on the licence, mention it.

Review: confirmed. 116 Co-Authored-By trailers (9+18+47+18+24), all noreply@anthropic.com. The title says 'All commits', but 116 of 129 is not all; the body has the right number.

#### L15. [low] Version 0.7.0 on HEAD has no tag, and tags stop at v0.4.0

Evidence: pyproject.toml:7 version = "0.7.0"; git tag -l gives v0.1.0-v0.4.0 only; HEAD is 18 commits ahead of origin/main. CHANGELOG.md mentions a publish only for 0.1.0 (line 55).

Recommendation: Before choosing the first version under the new licence, establish which of 0.5.0-0.7.0 were ever pushed or published. The Apache/non-commercial boundary should fall on a version number nobody has received yet.

Review: confirmed. pyproject.toml:7 is 0.7.0; tags stop at v0.4.0; HEAD is 18 ahead of origin/main. The open question it raises is answerable from the tree: origin/main:pyproject.toml reads 0.6.0, so 0.5.0 and 0.6.0 are pushed and only 0.7.0 is local.

#### L16. [low] Agent plans quote the Apache header 38 times

Evidence: docs/agent/plans/2026-09-23-provision.md (22 matching lines, e.g. 109-110), 2026-09-24-module-adoption.md (9), 2026-10-04-standalone-provision.md (7).

Recommendation: Leave them: they are records of work done under Apache-2.0. Exclude docs/agent/ and docs/archive/ from any search-and-replace, and from the header checker, so the pass does not rewrite history.

Review: confirmed. 'Licensed under the Apache' matches: 22 + 9 + 7 = 38 in the three plans. module-adoption.md has two more prose mentions of Apache (lines 18 and 588), which do not change the conclusion.

### Not checked

- PyPI itself: which sushicore versions are published and what licence metadata each shows. The claim rests on CHANGELOG.md line 55 and release.yml only.
- GitHub releases, forks and stars of SushiSystems/SushiCore; whether anyone has already forked the Apache-licensed code.
- Licences of rich, typer, click, tomli, pytest and setuptools were stated from memory, not read from installed package metadata, and their transitive dependencies (markdown-it-py, pygments, shellingham and others) were not enumerated.
- The full list of winget ids, vcpkg ports and direct-download URLs in sushicore/provision/packages/ and sushicore/provision/gpu/ beyond cuda.py, adapter_builder.py and base.deps.toml; each tool's licence was not looked up.
- Whether code in sushicore/provision/ that was moved from the hub repository carried a different header or author there.
- The 39 Markdown files were searched by keyword (apache, licence, license, copyright, pypi), not read in full; docs/agent/specs and reports were covered only by that search.
- Module docstring and symbol docstring conformance to source-comments beyond the licence block.
- Whether 'Sushi Systems' is a registered legal entity; nothing in the repository settles it.
- Tags' annotated messages and the content of commits between v0.4.0 and HEAD for licence-related changes.
- The untracked file docs/agent/plans/2026-09-25-hub-root-migration.md and the ignored .superpowers/ tree, apart from noting they repeat the Apache header.

## Command line

### Facts

- Entry points: none. D:/Projects/sushicore/pyproject.toml has no [project.scripts] and the package has no __main__.py; sushicore 0.7.0 is a library, as README.md line 12 states.
- Version required by consumers: all seven CLI pyproject files (sushistack/cli, sushiruntime/cli, sushiengine/cli, sushiai/cli, sushiblas/cli, sushidsp/cli, sushitrack/cli) pin `sushicore>=0.7.0`; pyproject.toml declares version 0.7.0.
- Framework: Typer over Click, optional. Hard dependencies are rich>=13 and tomli (<3.11); typer>=0.12 sits in the `typer` extra. Only sushicore/typer_help.py and sushicore/provision/commands.py (lazily, inside register_provision_commands) import Typer.
- Command tree sushicore registers (sushicore/provision/commands.py, register_provision_commands): setup, doctor, link, unlink. A binary install (ModuleProvision.is_binary) gets doctor alone.
- setup options: --dry-run, --yes (no short form), --toolchain NAME (repeatable, keys listed from selection.toolchain_keys()), --no-gpu. doctor: --for GROUP. link: --workspace PATH. unlink: --workspace PATH. No command takes a positional argument.
- Offered as classes but not registered as commands: Diagnostics.config_show / env_dump (sushicore/diag.py), ExecutableIndex for `run` (discovery.py), Runner (proc.py), CMakeDriver (cmake_driver.py). Each CLI declares its own `config`, `env`, `build`, `test`, `run` Typer commands and delegates.
- Help rendering: help_group(provider) in sushicore/typer_help.py returns a TyperGroup subclass that draws a HelpPage (logo on the root page, Title, Usage, command sections, Arguments, Options, Examples). A drawing failure logs one warning on `sushicore.help` and falls back to Typer's own help.
- Help panel grouping: by Typer's rich_help_panel, in order of first appearance; a command with none lands under `Commands` (help/from_click.py K_DEFAULT_GROUP). sushicore defines no panel names; the provision commands take the panel from ModuleProvision.panel. Examples come from the epilog, one per line, split at ' # '.
- Output rendering: Console facade (info, success, warn, error, command, header, fail_panel, table, progress, result, prompt) over a Renderer protocol with three backends: RichRenderer, PlainRenderer, JsonRenderer (one JSON event per line on stdout, raw Rich output routed to stderr). Event kinds: line, command, header, panel, table, progress, result, prompt (events.py).
- Machine mode is a property, not a flag: build_console(machine=True) or LazyConsole.machine = True. sushicore offers no --json option, no --describe catalogue and no root callback; hub defines both flags itself (sushistack/cli/sushihub/cli.py:54-57, sushihub/describe.py).
- Version flag: sushicore offers none and exports no __version__. Among the CLIs only se declares --version (sushiengine/cli/sushiengine/cli.py:114).
- Exit codes: setup 0 / 1 (cycle, lock timeout, failed step, failed required check) / 2 (missing module checkout, unknown toolchain); doctor 0 / 1 (required check failed or cycle) / 2 (unknown --for group); link and unlink 0 / 1 (LinkEditError) / 2 (no workspace). Runner returns the child's code, missing_exit_code (default 1) for a missing executable, 130 on Ctrl+C when catch_interrupt is set.
- Error reporting: console.error(one line) followed by typer.Exit(code) in the provision commands; ModuleConfig.find_project_root raises SystemExit(message) outside a checkout (module_config.py:75); Doctor.run turns any exception inside a check into a FAIL row; Runner prints a four-line 'Executable not found' hint.
- Colour: [cli] color = auto|always|never, SUSHI_CLI_COLOR, and NO_COLOR (wins over everything) in sushicore/config.py; auto means sys.stdout.isatty(). FORCE_COLOR and CLICOLOR are not read, and no --no-color option is offered. Themes: default (= sushiweb), mono, muted. Icon sets: text, emoji, minimal, none.
- Other environment the layer reads: SUSHI_CLI_THEME, SUSHI_CLI_ICONS, SUSHI_CLI_BACKGROUND, COLORFGBG, SUSHISTACK_HOME, SUSHISYSTEMS_HOME, SUSHISTACK_DEPS_DIR, and <PREFIX>_<TOOL> overrides derived from ModuleProfile.env_prefix.
- Windows handling: RichRenderer reconfigures stdout/stderr to UTF-8 and switches on virtual terminal processing (windows_console.py); the logo shows only on a UTF-8 terminal with 256 colours or more and colour on.
- Help string register: short imperative sentences ending in a period ('Show, don't change.', 'Skip the toolkit for this machine's GPU.'); command docstrings are one sentence starting with a verb. hub's own options use the same register.
- CLI documentation present in the repository: README.md and docs/README.md only. There is no CLI_GUIDE, no docs/guides/, no docs/getting_started/; docs/ holds README.md, CLAUDE.md, reference/CHANGELOG.md and agent/.

### Corrections from review

- Line citations into sushicore/provision/commands.py are off by 2 to 14 lines throughout. Correct values: register_provision_commands 247 (not 261); fragment default 90 (not 86); ModuleSink(root / 'cli') 208 (not 210); write_link 310 (not 315); clear_link 331 (not 337); --yes 265-266 (not 273-274); --toolchain 267-270 (not 277-279); --for help 281-282 (not 292); bad --for exit 289 (not 300); _run_setup returns at 192, 196, 203, 223, 225 (not 196, 200, 206, 227, 229); link 296-315 and unlink 317-340 (not 303-323 and 325-346). No conclusion changes.
- renderer.py: _level_from_prefix is at 242-248 (not 233-239), JsonRenderer.table at 290-299 (not 283), PlainRenderer.table at 207 (not 211).
- Fact 'Only typer_help.py and provision/commands.py import Typer' is incomplete: sushicore/typer_theme.py:20 imports typer.rich_utils (lazily), and build_console calls apply_typer_theme on every console build (__init__.py:70).
- docs/README.md mentions LazyConsole at lines 51-52 and 106, not 58 and 105.
- F2 recommendation says ui/table.py already colours the doctor's status words. K_STATUS_STYLES (ui/table.py:28-39) holds OK, FAIL, WARN and SKIPPED but not SKIP, and the doctor's word is 'skip' (doctor.py:94), so that state would lose its style.
- Minor: doctor.py GROUPS is on line 11 (not 10); console.py prompt id is on line 120 (not 122); pipeline.py program default is on line 53 (not 54); config.py tomllib.load is on line 59 (not 58) and workspace.py's on line 47 (42 is the def line); hub's _finish is at sushihub/cli.py:89 (not 91).
- Recomputed and correct: seven consumer pins of sushicore>=0.7.0; pyproject version 0.7.0 with no [project.scripts]; three files in docs/agent/specs, none named 2026-09-05-hub-design.md; command tree setup/doctor/link/unlink with the listed options; config/env line numbers in all six module CLIs.

### Findings

#### C1. [high] The shared offer stops at four commands; version, JSON mode, describe, config and env are left to each CLI

Evidence: D:/Projects/sushicore/sushicore/provision/commands.py:261 registers setup/doctor/link/unlink only. There is no shared root callback: --json and --describe exist only in D:/Projects/sushistack/cli/sushihub/cli.py:54-57, --version only in D:/Projects/sushiengine/cli/sushiengine/cli.py:114. `config` and `env` are redeclared as Typer commands in six CLIs (sushiruntime cli.py:262/273, sushiengine cli.py:839/852, sushiai cli.py:231/242, sushiblas cli.py:150/161, sushidsp cli.py:108/119, sushitrack cli.py:338/353) around sushicore.diag.Diagnostics.

Recommendation: Owner decision on the interface: add a registration brick per shared surface, shaped like register_provision_commands (root options --version/--json/--describe, and config/env from Diagnostics), so a CLI gets the flag by calling one function and cannot be the one without it.

Review: confirmed. commands.py registers only setup/doctor/link/unlink (register_provision_commands is at line 247, not 261). --json/--describe exist only at sushihub/cli.py:54-57, --version only at sushiengine cli.py:114; config/env are declared at the cited lines in all six module CLIs. Recommendation is brick-shaped and correctly flagged as an owner decision.

#### C2. [high] JSON output of doctor carries Rich markup in the table event

Evidence: D:/Projects/sushicore/sushicore/provision/doctor.py:91-96 maps states to '[success]ok[/success]', '[error]FAIL[/error]' and line 131 puts that string in the table row; D:/Projects/sushicore/sushicore/renderer.py:283 (JsonRenderer.table) emits rows unchanged, and PlainRenderer.table (line 211) prints them raw. The result payload on doctor.py:140 is clean, so one run reports the same state two ways.

Recommendation: Pass the bare state word to console.table; ui/table.py already colours status words (OK, FAIL, WARN, SKIPPED) from the theme, so the markup is not needed.

Review: confirmed. doctor.py:90-95 holds the markup map and line 130 puts it in the row; JsonRenderer.table (renderer.py:290-299) and PlainRenderer.table (207-220) pass cells through unchanged. The recommendation is incomplete: ui/table.py K_STATUS_STYLES has SKIPPED but not SKIP, so a bare 'skip' would lose its dim style unless the word or the map changes. No module CLI sets machine mode today, so only hub can reach the JSON path.

#### C3. [high] The level of a JSON line event depends on the user's icon set

Evidence: D:/Projects/sushicore/sushicore/renderer.py:233-239 (_level_from_prefix) derives the level from the icon text, and Console.error passes only style and icon (console.py:73-75). With SUSHI_CLI_ICONS=emoji, minimal or none, every error and warning line is emitted as level "info". docs/README.md lines 126-129 document this as behaviour.

Recommendation: Carry the level through the Renderer.line call (or add one method per level) so the machine stream does not change with a cosmetic setting.

Review: confirmed. renderer.py:242-248 derives the level from the icon text and console.py:61-75 passes only style and icon; the emoji, minimal and none sets (icons.py) name no level, so every line becomes 'info'. docs/README.md:127-130 documents it. The default text set ([INFO]/[SUCCESS]/[WARN]/[ERROR]) works.

#### C4. [high] Child processes inherit stdout, so machine mode does not keep stdout to JSON events

Evidence: docs/README.md:111 promises 'One JSON object per line, UTF-8, no other bytes on stdout'. Runner.run (D:/Projects/sushicore/sushicore/proc.py:96) calls subprocess.run with no stdout redirection and its docstring says the child inherits stdout. The same holds in provisioning: provision/steps.py:619 (Visual Studio Build Tools installer), provision/system.py:51 and 71 (bash -c), provision/toolchains/oneapi.py:63 (curl). The sibling helpers packages/base.py:23-31 and Runner.run_drained (proc.py:122-131) pipe the child and re-emit through console.console, which is stderr in machine mode, so the layer has two shapes for the same job. toolchains/adaptivecpp.py:60-69 also asks through console.console.print plus input() beside its console.prompt branch.

Recommendation: Make one child-process brick the only way the layer spawns a streaming child (the run_drained shape: pipe, re-emit through the console), and have the inheriting call sites use it; where a child truly needs the terminal, route its stdout to stderr when console.is_machine().

Review: found by review.

#### C5. [medium] setup, link and unlink end without a result event in machine mode

Evidence: D:/Projects/sushicore/sushicore/provision/commands.py: only Doctor.render emits console.result (doctor.py:147). _run_setup returns 1 or 2 at lines 196, 200, 206, 227, 229 after console.error alone; doctor's bad --for exits 2 at line 300 with no result; link (303-323) and unlink (325-346) never call console.result. hub's _finish (sushistack/cli/sushihub/cli.py:91) emits a result on every exit.

Recommendation: Give the provision commands one exit helper that emits result(ok, payload) and raises typer.Exit, the same shape as hub's _finish, and move it into sushicore so hub uses it too.

Review: confirmed. Only Doctor.render (doctor.py:147) calls console.result. _run_setup returns at commands.py:192, 196, 203, 223, 225 after console.error alone (audit's line numbers are 4 off); doctor's bad --for exits at 289; link and unlink (296-340) never emit a result. hub's _finish is at sushihub/cli.py:89-99.

#### C6. [medium] Diagnostics and the executable picker bypass the Console facade

Evidence: D:/Projects/sushicore/sushicore/diag.py:113-128 and 147-170 build rich.table.Table directly and print through console.console, so `config` and `env` draw framed tables (the rest of the layer is frameless, ui/table.py) and in machine mode go to stderr with no table event. D:/Projects/sushicore/sushicore/discovery.py:118-137 hard-codes column styles 'cyan', 'bold', 'dim' and asks through rich IntPrompt, which emits no prompt event and blocks a JSON reader.

Recommendation: Route the three tables through console.table and the choice through console.prompt.

Review: confirmed. diag.py:113-128 and 147-170 build rich.table.Table and print through console.console, which in machine mode is JsonRenderer.raw on stderr (renderer.py:263). discovery.py:118-137 hard-codes cyan/bold/dim and uses IntPrompt.ask.

#### C7. [medium] An unknown theme or icon name, or a malformed config file, reaches the user as a traceback

Evidence: D:/Projects/sushicore/sushicore/__init__.py:67-68 calls get_theme / get_icon_set, which raise ValueError (theme.py:109, icons.py:43) for e.g. SUSHI_CLI_THEME=foo; config.py:58 (_read_toml) and workspace.py:42 (read_toml) let tomllib.TOMLDecodeError out. Nothing between LazyConsole.get (cli_console.py:65-69) and the command body catches either. `color` and `background` fall back silently on a bad value (config.py:115-118), so the four appearance settings do not fail the same way.

Recommendation: Define one module base error for the presentation layer and catch it at the entry point with one line and a non-zero exit; decide one policy for a bad appearance value (fall back with a warning, or fail) and apply it to all four keys.

Review: confirmed. __init__.py:68-69 call get_theme/get_icon_set, which raise ValueError (theme.py:109, icons.py:43); config.py:59 and workspace.py:47 call tomllib.load unguarded; LazyConsole.get (cli_console.py:64-70) catches nothing. color/background fall back silently at config.py:115-118. The help path alone is guarded (typer_help.py:86).

#### C8. [medium] Two ways of reporting 'not inside a project'

Evidence: D:/Projects/sushicore/sushicore/module_config.py:75 raises SystemExit(message), which Python prints unstyled to stderr with exit 1 and no JSON event; every other failure in provision/commands.py goes through console.error plus typer.Exit. _run_setup (line 189-190) and _run_doctor (line 173-174) call project_root()/load_config() unguarded, so `setup` and `doctor` outside a checkout take the SystemExit path.

Recommendation: Raise a typed error from find_project_root and let the entry point print it through the console; keep the SystemExit only where LazyConsole.sources depends on it, or change that to the typed error as well.

Review: confirmed. module_config.py:75 raises SystemExit(message). _run_doctor calls load_config/project_root at commands.py:169-170 and _run_setup at 186-187 (not 173-174 and 189-190) with no guard; link and unlink call project_root() unguarded too (304, 325), which the audit does not mention.

#### C9. [medium] docs/README.md contradicts the code and the front README on how sushicore is installed

Evidence: D:/Projects/sushicore/docs/README.md:192 'sushicore is not published to any package index'; D:/Projects/sushicore/README.md:9 'pip install sushicore'; docs/reference/CHANGELOG.md '2026-09-22 — Published 0.1.0 to PyPI'; all seven CLIs depend on `sushicore>=0.7.0` as a normal requirement. docs/README.md:208 says `hub link sushicore` records in modules.local.toml, which hub names LEGACY_MODULES_FILE (sushistack/cli/sushihub/config.py:61); workspace.py:128 says [modules] lives in workspace.toml.

Recommendation: Rewrite the Installing section of docs/README.md from the current state: PyPI package, version floor, workspace.toml registry.

Review: confirmed. docs/README.md:192 says not published; README.md:9 says pip install sushicore; CHANGELOG.md:55 records the PyPI publish; all seven CLIs pin sushicore>=0.7.0. docs/README.md:208 names modules.local.toml, which sushihub/config.py:61 calls LEGACY_MODULES_FILE; workspace.py:127 puts [modules] in workspace.toml.

#### C10. [medium] The manual's usage example is the pattern cli_console.py was written to remove

Evidence: D:/Projects/sushicore/docs/README.md:165-173 shows `_cfg_dir = config_dir()` and `console = build_console(...)` at import time. D:/Projects/sushicore/sushicore/cli_console.py:1-15 states that this makes every invocation fail outside a checkout and that LazyConsole exists so no CLI does it. LazyConsole appears in docs/README.md only in passing (lines 58 and 105); README.md does not mention it.

Recommendation: Replace the example with the LazyConsole wiring (module __getattr__ = lazy.attribute, help_group(lazy.get)).

Review: confirmed. docs/README.md:165-185 shows config_dir() and build_console(...) at import; cli_console.py:1-14 says that pattern breaks every invocation outside a checkout. LazyConsole appears in docs/README.md at lines 51-52 and 106 (not 58 and 105) and nowhere in README.md.

#### C11. [medium] docs/README.md describes a three-CLI presentation layer and omits half of what the package offers

Evidence: D:/Projects/sushicore/docs/README.md:3-7 names `sr`, `se`, `hub` and 'three hardcoded console.py files'; seven CLIs consume it. The manual has no section for register_provision_commands, Diagnostics, ExecutableIndex, Runner, CMakeDriver or ModuleProfile; README.md covers provisioning but not exit codes for link/unlink, nor the `config`/`env` helpers.

Recommendation: Document the full shared CLI surface in one reference page: commands, options, exit codes, environment variables, event schema.

Review: confirmed. docs/README.md:3-7 names sr, se, hub and 'three hardcoded console.py files'; grep finds no mention of register_provision_commands, Diagnostics, ExecutableIndex, Runner, CMakeDriver or ModuleProfile in it. README.md:74-82 covers the provision commands without link/unlink exit codes.

#### C12. [medium] link accepts any --workspace path and edits two files with no rollback

Evidence: D:/Projects/sushicore/sushicore/provision/commands.py:305-314: the target from --workspace or SUSHISTACK_HOME is never checked for the .sushistack marker (only the walk-up branch of _resolve_workspace, 229-236, checks it). write_module (workspace.py:142-157) then runs target.parent.mkdir(parents=True), so `link --workspace <typo>` creates a new .sushistack/workspace.toml there and reports success. write_link (310) runs before write_module (314), and write_module sits outside the try: a malformed workspace.toml raises tomllib.TOMLDecodeError from read_toml (workspace.py:47) as a traceback after the [link] pointer is already written. unlink has the same order at 331-336.

Recommendation: Validate the resolved workspace with has_marker before any write and exit 2 with the existing no-workspace line; wrap both edits in one operation that catches the module's own error type and leaves neither file changed on failure.

Review: found by review.

#### C13. [medium] The manual's config schema and precedence omit the background key the code and the same page define

Evidence: D:/Projects/sushicore/docs/README.md:140-158: the [cli] schema block lists theme, icons, color and the precedence line lists SUSHI_CLI_THEME / ICONS / COLOR, while config.py:16 and 110-111 define `background` and SUSHI_CLI_BACKGROUND, and docs/README.md:68-73 describes them in another section. A reader of the schema section gets three of four keys.

Recommendation: Add background and SUSHI_CLI_BACKGROUND to the schema block and the precedence line, or fold both into the single reference page F10 asks for.

Review: found by review.

#### C14. [low] Prompt event id in the manual does not match the code

Evidence: D:/Projects/sushicore/docs/README.md:123 shows "id": "confirm-1"; D:/Projects/sushicore/sushicore/console.py:122 generates f"prompt-{n}". The manual says the desktop application's schema depends on these keys.

Recommendation: Correct the example to prompt-1.

Review: confirmed. docs/README.md:123 shows "confirm-1"; console.py:120 generates f"prompt-{n}" (line 120, not 122).

#### C15. [low] Three citations point at a design document that is not in this repository

Evidence: docs/agent/specs/2026-09-05-hub-design.md is cited at D:/Projects/sushicore/docs/README.md:132, sushicore/renderer.py:8 and sushicore/profile.py:27. D:/Projects/sushicore/docs/agent/specs/ holds only 2026-09-21-terminal-components-design.md, 2026-09-23-provision-design.md and 2026-10-04-standalone-provision-design.md; the cited file exists in D:/Projects/sushistack/docs/agent/specs/.

Recommendation: Move the event-schema section into a sushicore document (the schema is sushicore's public format) and cite that.

Review: confirmed. The path is cited at docs/README.md:132, renderer.py:8 and profile.py:27; docs/agent/specs in sushicore holds three other files; the cited file exists in D:/Projects/sushistack/docs/agent/specs/.

#### C16. [low] doctor --for does not list its groups, and the groups include one module's vocabulary

Evidence: D:/Projects/sushicore/sushicore/provision/commands.py:292 help is 'Restrict the report to one check group.' with no values, while --toolchain on line 277-279 lists its keys. D:/Projects/sushicore/sushicore/provision/doctor.py:10 fixes GROUPS = ('build', 'test', 'infer', 'eval'); infer and eval are sushiai concerns, and a new group needs an edit to the shared tuple.

Recommendation: List the groups in the help text the way --toolchain does; let a module contribute its groups through ModuleProvision instead of the shared constant (owner decision on the interface).

Review: confirmed. commands.py:281-282 help names no groups while --toolchain (267-270) lists its keys; doctor.py:11 fixes GROUPS = build, test, infer, eval (line 11, not 10). README.md:75-76 does list them. Recommendation is brick-shaped and marked as an owner decision.

#### C17. [low] Option shape differs from hub for the same flag

Evidence: D:/Projects/sushicore/sushicore/provision/commands.py:273-274 declares `--yes` without a short form; hub declares `--yes, -y` (sushistack/cli/sushihub/cli.py:279, 340). No shared context_settings adds `-h` beside `--help`.

Recommendation: Fix one spelling for the confirmation flag and the help flag across the shared commands and hub.

Review: confirmed. commands.py:265-266 declares --yes alone; sushihub/cli.py:279 and 340 declare --yes, -y. No help_option_names adds -h anywhere in sushicore; sushiai sets it to [] on three commands.

#### C18. [low] The `cli/` directory and the default program name are hard-coded in the shared commands

Evidence: D:/Projects/sushicore/sushicore/provision/commands.py:86 (fragment = 'cli/sushistack.deps.toml'), 210 (ModuleSink(root / 'cli')), 315 (write_link(root / 'cli')), 337 (clear_link(root / 'cli')), although each CLI already owns a config_dir resolver (cli_console.py LazyConsole, diag.py ConfigModule.config_dir). provision/pipeline.py:54 defaults InstallContext.program to 'hub', and proc.py:82 tells every user to run `<program> config`, a command sushicore does not register.

Recommendation: Take the config directory from ModuleProvision; drop the 'hub' default so a caller must name its program.

Review: confirmed. 'cli' is hard-coded at commands.py:90, 208, 310, 331 (audit cites 86, 210, 315, 337); pipeline.py:53 defaults program to 'hub'; proc.py:82 tells the user to run `<program> config`.

#### C19. [low] An absolute path on the owner's machine in shipped source

Evidence: D:/Projects/sushicore/sushicore/theme.py:68 comment cites 'D:/Projects/sushiweb/src/styles/global.css'.

Recommendation: Cite the repository and relative path, or a design document.

Review: confirmed. theme.py:68 comment reads 'D:/Projects/sushiweb/src/styles/global.css'.

#### C20. [low] `config` reports the wrong source layer for a value

Evidence: D:/Projects/sushicore/sushicore/diag.py:85-90 (_source_of) returns 'config.toml' for any key found in either config.toml or config.local.toml, and never names the linked workspace's [tool] table that module_config layers in; the command's stated purpose (diag.py:3-5) is to say where each value came from.

Recommendation: Track the file each key was last set by and print that name.

Review: confirmed. diag.py:85-90 returns 'config.toml' for a key found in either file of _CONFIG_FILES and has no branch for the linked workspace's [tool] table.

#### C21. [low] README does not say the provision commands need the typer extra

Evidence: D:/Projects/sushicore/README.md:9 gives `pip install sushicore` and lines 27-41 use typer and register_provision_commands; pyproject.toml puts typer under [project.optional-dependencies] typer. commands.py:263 and typer_help.py:15 import typer.

Recommendation: State `pip install sushicore[typer]` for a CLI that uses help_group or the provision commands.

Review: confirmed. README.md:9 gives plain `pip install sushicore`; pyproject.toml puts typer under the `typer` extra; typer_help.py:15 imports typer.core at module level and commands.py:249 imports typer inside the function (not 263).

### Not checked

- The seven tool CLIs were only grepped for sushicore pins, flag names and which shared classes they import; their command trees and local duplicates are other agents' scope and were not read.
- sushicore/provision/steps.py (820 lines), probe.py, checks.py, closure.py, selection.py, fragments.py, registry.py, system.py, and everything under provision/gpu, provision/packages and provision/toolchains: only grepped for raise/except sites, not read line by line. User-facing message wording there is unreviewed.
- sushicore/cmake_driver.py, cmake_cache.py, build_env.py, toolchain_args.py, stack_config.py, module_config.py (beyond signatures), config_base.py, deps_fragment.py, markup.py, brand.py, help/logo_choice.py and every file under sushicore/ui/ were not read.
- tests/ was not read; no claim is made about test coverage of the CLI surface.
- docs/agent/ plans, specs and reports were not read against the code.
- No CLI was run, so rendered help output, actual exit codes and traceback behaviour are inferred from source, not observed.
- Whether sushicore 0.7.0 is actually on PyPI was not checked (no network access used).
- Licence headers and the documentation-architecture gaps (missing CONTRIBUTING, GLOSSARY, KNOWN_ISSUES, stale docs/CLAUDE.md) belong to other dimensions and are not reported here.

## Documentation

### Facts

- Tracked tree: 212 files. docs/ holds 5 folders only: docs/agent/{specs,plans,reports} and docs/reference. No tools/ folder, so no check_docs_layout.py or check_source_comments.py.
- PRESENT: README.md, docs/README.md, docs/reference/CHANGELOG.md, docs/agent/specs (3 files), docs/agent/plans (4 tracked + 1 untracked), docs/agent/reports (28 files), LICENSE (Apache-2.0 text).
- MISSING: docs/CONTRIBUTING.md, docs/DOCUMENTATION_STYLE_GUIDE.md, docs/getting_started/, docs/architecture/, docs/modules/, docs/guides/, docs/reference/GLOSSARY.md, docs/reference/KNOWN_ISSUES.md, docs/design/ (so no design/README.md and no REMAINING_WORK.md), docs/archive/.
- MISSING per-module READMEs: none of sushicore/, sushicore/provision/, sushicore/provision/gpu/, sushicore/provision/packages/, sushicore/provision/toolchains/, sushicore/ui/, sushicore/help/, tests/ carries a README.md.
- No place in the architecture: docs/CLAUDE.md (agent instructions inside docs/). It is not a document; by convention it belongs at the repository root as CLAUDE.md, or is deleted in favour of the global rules.
- docs/agent/ uses the flat specs|plans|reports layout with lower-kebab dated names (global CLAUDE.md shape). The `documentation` skill instead requires docs/agent/<YYYY_MM_DD>_<WORK_NAME>/{SPEC,PLAN,REPORT}.md; the two yardsticks disagree and the repo follows the CLAUDE.md one.
- docs/agent/reports holds 28 files: 24 per-task reports and 3 review-wave reports for one piece of work (terminal components), plus 2026-09-22-cleanup-task-0.md and 2026-09-22-wave-3-task-1.md. Provision, module-adoption and standalone-provision work have no report at all.
- docs/agent totals 13 594 lines across 37 files; the manual (docs/README.md) is 221 lines and the changelog 56.
- Untracked at D:/Projects/sushicore: docs/agent/plans/2026-09-25-hub-root-migration.md (337 lines), cited by two tracked documents. Untracked and ignored: .superpowers/sdd/2026-09-23-provision/ (review reports, diffs, probe scripts).
- Versions: pyproject.toml says 0.7.0; git tags are v0.1.0 to v0.4.0 only; release commits exist for 0.5.0 (a5fa5ae) and 0.7.0 (c6d5f55); hub's cli/pyproject.toml requires sushicore>=0.7.0.
- Changelog: 51 entries, none over 240 characters, none nested, none multi-sentence. No `## Unreleased` or `## vX.Y.Z` heading; 39 of 51 entries carry no `<scope>:` prefix.
- Verified true in README.md: ModuleProvision field names (commands.py:85-94), the four commands and their flags (--dry-run, --yes, --toolchain, --no-gpu, --for, --workspace), doctor groups (doctor.py:11), bind_root, search_roots, bind_console, locate_sibling, dependency_roots, base fragment contents.
- Verified true in docs/README.md: theme presets default/mono/muted, icon presets text/emoji/minimal/none, SUSHI_CLI_THEME/ICONS/COLOR/BACKGROUND and NO_COLOR (config.py:104-112), JsonRenderer/PlainRenderer/RichRenderer, event_line, help_group.
- Neither README.md nor docs/README.md contains a single Markdown link; every cross-reference is a backticked path.

### Corrections from review

- docs/agent holds 36 Markdown files on disk (3 specs, 5 plans, 28 reports), 35 of them tracked, not 37. The 13 594-line total is right and includes the untracked plan.
- docs/agent/reports holds 23 per-task terminal-components reports (tasks 1-10, 12-19, 21-25), not 24. With 3 review-wave reports and 2 others the total of 28 is right; the audit's own breakdown (24 + 3 + 2) sums to 29.
- Changelog entries without a `<scope>:` prefix: 38 of 51, not 39. 13 entries carry one (lines 6-17 and 24).
- sushicore/provision ships 43 tracked files (git ls-files sushicore/provision), not 50.
- F3 lists specs 2026-09-21 and 2026-09-23 as citing non-existent docs/design and docs/guides. Both passages (spec 09-21 line 200, spec 09-23 line 170) say that sushicore lacks those folders; they are not broken citations.
- README.md line 53 is 122 characters, not 119.
- docs/README.md is 220 lines by wc -l (221 text lines, the last without a newline); the audit uses 221.

### Findings

#### D1. [high] docs/README.md is a stale second front door, not a manual index

Evidence: D:/Projects/sushicore/docs/README.md lines 1-7 open with a product description ("Shared, config-driven CLI presentation layer ... (`sr`, `se`, `hub`)") and then carry the whole manual inline (Design, Help screens, Tables, Machine-readable output, Config schema, Installing). It links to no other document: not docs/reference/CHANGELOG.md, not any of the 3 specs, 5 plans or 28 reports. It describes only the presentation layer; `sushicore.provision`, `workspace`, `config_base`, `cmake_driver`, `stack_config`, `module_config`, `profile`, `deps_fragment` are absent, while root README.md line 3 names seven CLIs and five jobs.

Recommendation: Rewrite docs/README.md as an index that reaches every document. Move its content by the placement questions: component descriptions to module READMEs (sushicore/ui, sushicore/help), config schema and JSON event vocabulary to docs/reference/, the help-screen and console how-to to docs/guides/, installing to docs/getting_started/.

Review: confirmed. Read docs/README.md in full: lines 3-7 are a product description, the manual is inline, there is no link or citation to CHANGELOG.md or any agent document, and provision, workspace, config_base, cmake_driver, stack_config, module_config, profile and deps_fragment are not mentioned.

#### D2. [high] Installing section contradicts the code, the root README and the changelog

Evidence: D:/Projects/sushicore/docs/README.md:192 "sushicore is not published to any package index". Against it: README.md:9 `pip install sushicore`; docs/reference/CHANGELOG.md:55 "Published 0.1.0 to PyPI"; .github/workflows/release.yml publishes on every `v*` tag via pypa/gh-action-pypi-publish; D:/Projects/sushistack/cli/pyproject.toml:17 depends on `sushicore>=0.7.0`. Lines 196-215 describe a bootstrap that clones into `<workspace>/sushicore`, editable pipx injection, `hub link sushicore`, `modules.local.toml` and `SUSHICORE_DIR`; `SUSHICORE_DIR` occurs in no Python source in sushicore or sushistack (only in sushistack/cli/README.md), and sushistack/cli/sushihub/config.py:61 names `modules.local.toml` LEGACY_MODULES_FILE.

Recommendation: Replace the section with the PyPI install and an editable install for contributors; drop the checkout-injection story, SUSHICORE_DIR and modules.local.toml. Fix the same stale text in sushistack/cli/README.md in the hub pass.

Review: confirmed. docs/README.md:192 against README.md:9, CHANGELOG.md:55, release.yml:5/38 and sushistack/cli/pyproject.toml:17 all check out; SUSHICORE_DIR appears in no .py file. Also stale and not caught: line 200 lists hub status states fetched/linked/sibling/missing, while sushistack/cli/sushihub/describe.py:23 has cloned/linked/binary.

#### D3. [high] Cited paths that do not resolve

Evidence: docs/README.md:132 cites `docs/agent/specs/2026-09-05-hub-design.md` (absent; the hub spec lives in another repository). docs/CLAUDE.md:8 cites `docs/slop/` and `docs/api/` (neither exists). docs/agent/specs/2026-10-04-standalone-provision-design.md cites `docs/design/WORKSPACE_DECOUPLING.md` and `docs/getting_started/INSTALL.md` (neither exists here), and at line 14 `../plans/2026-09-25-hub-root-migration.md`, which exists only untracked, so the link is broken in every clone. docs/agent/plans/2026-10-04-standalone-provision.md:1366 cites the same untracked file. Specs 2026-09-21 and 2026-09-23 cite `docs/design/` and `docs/guides/`, which do not exist.

Recommendation: Name the owning repository in every cross-repository citation (for example `sushistack: docs/...`), commit or drop the untracked hub-root-migration plan after the owner decides, and correct docs/README.md:132 to the real location of the JSON event design.

Review: confirmed. docs/README.md:132, docs/CLAUDE.md:8, standalone spec lines 14 and 170, and plan line 1366 are real. One part is wrong: specs 2026-09-21 (line 200) and 2026-09-23 (line 170) name docs/design and docs/guides in order to say sushicore lacks them, so those two are not broken citations.

#### D4. [high] Skeleton missing: no CONTRIBUTING, style guide, glossary, known issues, design, archive or manual folders

Evidence: Absent under D:/Projects/sushicore/docs: CONTRIBUTING.md, DOCUMENTATION_STYLE_GUIDE.md, getting_started/, architecture/, modules/, guides/, design/, archive/, reference/GLOSSARY.md, reference/KNOWN_ISSUES.md. docs/CLAUDE.md:7 states "this repo has no CONTRIBUTING.md of its own" and defers to sushiruntime.

Recommendation: Build the skeleton as its own approved task, per the global rule for a repository that lacks the shape. The content for the first pages already exists inside docs/README.md and README.md and needs moving, not writing.

Review: confirmed. find docs -type d returns only agent/{plans,reports,specs} and reference; docs/reference holds CHANGELOG.md alone; docs/CLAUDE.md:7 quote matches.

#### D5. [high] No design documents and no backlog; live intent sits in docs/agent/specs

Evidence: docs/design/ and docs/design/REMAINING_WORK.md do not exist. docs/agent/specs/2026-09-23-provision-design.md:38 says "Out of scope, recorded as backlog" with no backlog in this repository to record it in; docs/agent/specs/2026-10-04-standalone-provision-design.md:207 has an "Out of scope" section. The standalone-provision programme is tracked in sushistack's design folder (commit 4adc055 "list the standalone provisioning programme in the backlog"), so sushicore's open work is readable only from another repository.

Recommendation: Create docs/design/README.md and docs/design/REMAINING_WORK.md. Give provisioning one design document with a status line, and either hold sushicore's share of the backlog here or state in REMAINING_WORK.md that the programme backlog is sushistack's, with the path.

Review: confirmed. No docs/design. Spec 2026-09-23 line 38 and spec 2026-10-04 line 207 read as quoted; sushistack docs/design/REMAINING_WORK.md:53 carries the sushicore.provision programme and commit 4adc055 is in sushistack's log.

#### D6. [medium] Spec status lines are stale against shipped code

Evidence: docs/agent/specs/2026-09-23-provision-design.md:3 "**Status:** Draft, awaiting owner review." while sushicore/provision/ ships 50 files and CHANGELOG.md:26 records it added on 2026-09-23. docs/agent/specs/2026-09-21-terminal-components-design.md:3 "Approved" although sushicore/ui, sushicore/help and typer_help.py are shipped. docs/agent/specs/2026-10-04-standalone-provision-design.md:3 "Design approved 2026-10-04" although sushistack commit 51f6bde marks the module wave landed. None uses the `Open - phase n of m` / `Shipped` form.

Recommendation: Set each status to the real state in the required form: terminal components and provision `Shipped`, standalone provisioning `Open` with its phase.

Review: confirmed. Line 3 of all three specs reads as quoted (Approved / Draft, awaiting owner review / Design approved 2026-10-04). The provision file count is 43 tracked, not 50, which does not change the conclusion. The Open/Shipped form is a rule for design documents, so the defect is the stale status, not the form.

#### D7. [medium] Changelog has no release sections and cannot be matched to versions

Evidence: D:/Projects/sushicore/docs/reference/CHANGELOG.md is one flat list from line 6 to 56 with no `## Unreleased` or `## vX.Y.Z - date` heading, though the package has moved 0.1.0 to 0.7.0 (pyproject.toml:7). No entry records the 0.2.0 to 0.7.0 releases; line 55 mentions only 0.1.0. Tags stop at v0.4.0 while pyproject says 0.7.0 and release commits exist for 0.5.0 and 0.7.0, and no 0.6.0 release commit or tag is visible. docs/archive/changelog/ does not exist.

Recommendation: Group the entries under release headings that match the tags, open `## Unreleased`, move older releases to docs/archive/changelog/. Ask the owner about the missing v0.5.0 to v0.7.0 tags, since release.yml publishes only on a tag push; that is a release question, not a documentation edit.

Review: confirmed. CHANGELOG.md is one flat list, lines 6-56, with no ## heading; tags are v0.1.0-v0.4.0; pyproject.toml:7 is 0.7.0; release commits exist only for 0.5.0 (a5fa5ae) and 0.7.0 (c6d5f55), none for 0.6.0.

#### D8. [medium] Changelog entries out of order, without scope, and one that states a reason

Evidence: CHANGELOG.md lines 27-54 are not newest first: line 27 is 2026-09-21, lines 28-32 are 2026-09-22, lines 33-49 are 2026-09-21, lines 50-56 are 2026-09-22. Lines 18-23 and 25-56 carry no `<scope>:` prefix (39 of 51 entries). Line 28 gives a reason: "since Typer 0.27 no longer installs it"; line 31 another: "which garbled true-colour codes on Windows"; line 29 and 30 end in "so ..." clauses. The file's own preamble (lines 3-4) omits the scope rule.

Recommendation: Sort each section newest first, prefix each entry with its commit scope (help, ui, provision, config, workspace, proc, cmake), and cut the reason clauses from lines 28-31, 54.

Review: confirmed. Date order at lines 27-56 is as described; reason clauses at lines 28, 29, 30, 31 and 54 are present. The count of entries without a scope is 38, not 39 (lines 18-23 and 25-56).

#### D9. [medium] docs/CLAUDE.md is misplaced, describes another repository and breaks register

Evidence: D:/Projects/sushicore/docs/CLAUDE.md:8 tells the reader to skip `docs/slop/` and `docs/api/` "the generated Doxygen page" (neither exists; this is a Python package). Line 41 says builds go through "`se build`, `se editor`", commands of SushiEngine; sushicore has no CLI (README.md:12) and its CI runs `python -m pytest tests -q`. Line 7 points at sushiruntime's CONTRIBUTING.md. Line 49 ends "love you boss, kolay gelsin." A CLAUDE.md under docs/ is not loaded as project instructions from the repository root.

Recommendation: Remove it from docs/. If the repository needs project instructions, write a root CLAUDE.md with sushicore's own facts (pytest command, no CLI, PyPI release by tag) and leave the rest to the global rules. Deleting a file the agent did not create needs the owner's approval.

Review: confirmed. docs/CLAUDE.md lines 7, 8, 41 and 49 read as quoted; docs/slop and docs/api are absent; the repo has no CLI and no root CLAUDE.md. The recommendation correctly routes deletion through the owner.

#### D10. [medium] Agent reports break the one-report-per-work rule and three pieces of work have none

Evidence: D:/Projects/sushicore/docs/agent/reports/ holds 24 `2026-09-21|22-terminal-components-task-N.md` files (tasks 11 and 20 absent) and three `...-review-wave-{2,4,6}.md` files for one piece of work; the documentation skill says a second review round replaces the first report. No report exists for 2026-09-23-provision, 2026-09-24-module-adoption or 2026-10-04-standalone-provision; the provision review reports sit untracked in .superpowers/sdd/2026-09-23-provision/ (final-review.md, final-rereview.md, final-fix-report.md, progress.md). 2026-09-22-cleanup-task-0.md and 2026-09-22-wave-3-task-1.md name no work that has a spec or plan here.

Recommendation: Merge the terminal-components reports into one report, and, the work being shipped, move that spec, plan and report to docs/archive/. Decide with the owner whether the .superpowers provision reports are consolidated into a tracked report or discarded. Settle first which agent layout wins (flat specs|plans|reports or one folder per work), since CLAUDE.md and the documentation skill differ.

Review: confirmed. 28 report files, tasks 11 and 20 absent, three review-wave files, no report for provision, module-adoption or standalone-provision; .superpowers/sdd/2026-09-23-provision holds final-review.md, final-rereview.md, final-fix-report.md and progress.md. The per-task count is 23, not 24.

#### D11. [medium] Plans are frozen with every checkbox open and carry tool boilerplate

Evidence: Unchecked `- [ ]` counts: 2026-09-21-terminal-components.md 44, 2026-09-23-provision.md 74, 2026-09-24-module-adoption.md 65, 2026-10-04-standalone-provision.md 44; checked `- [x]` count is 0 in all, although the first three are shipped per the changelog. Each plan's line 3 reads "> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development ...". Three plans exceed 1 500 lines (2493, 1562, 1817). 2026-09-24-module-adoption.md plans changes to `st` and `sd`, which are other repositories.

Recommendation: Archive the shipped plans as they are instead of correcting them, and record the true state in the design status and changelog. For open work, keep the plan true as tasks land. Drop the superpowers header from future plans.

Review: confirmed. Unchecked counts 44/74/65/16/44 and zero checked in all five plans reproduced; line 3 superpowers header present in all five; line counts 2493, 1562, 1817 match. The 1 500-line limit in the skill is for design documents, so the size is context, not a rule breach.

#### D12. [medium] No module README anywhere; module facts live in the two front doors

Evidence: No README.md under D:/Projects/sushicore/sushicore/ or any of its packages (provision, provision/gpu, provision/packages, provision/toolchains, provision/manifests, ui, help) or under tests/. The provisioning facts (ModuleProvision fields, flags, exit codes, link pointer) are in README.md lines 24-82; the ui and help facts are in docs/README.md lines 30-102.

Recommendation: Add sushicore/provision/README.md, sushicore/ui/README.md and sushicore/help/README.md and move those facts there; keep the root README to what the package is, how to install it, and where the manual is.

Review: confirmed. The only README.md files in the tree are README.md and docs/README.md (plus .pytest_cache); README.md lines 24-82 and docs/README.md lines 30-102 hold the module facts.

#### D13. [medium] Root README is overloaded and its module table is incomplete

Evidence: D:/Projects/sushicore/README.md is 84 lines, 59 of them (24-82) a provisioning reference. The table at lines 15-22 omits shipped modules: `build_env`, `stack_config`, `module_config`, `profile`, `deps_fragment`, `discovery`, `diag`, `config`, `markup`, `cli_console`, `terminal_background`, `windows_console`, `typer_theme`, and `provision` itself. Line 3 says the CLIs import it for "the same five things" while the Provisioning section is a sixth. Line 53 is one unwrapped 119-character line in a file wrapped at 100. Line 84 cites `docs/README.md` and `LICENSE` without links and gives no licence name.

Recommendation: Cut the README to: what it is, install, a complete module table that links to module READMEs, a link to docs/README.md, and the licence by name. Update the licence line together with the licence change this programme decides.

Review: confirmed. README.md is 84 lines; the table at lines 15-22 omits build_env, stack_config, module_config, profile, deps_fragment, discovery, diag, config, markup, cli_console, terminal_background, windows_console, typer_theme (all present in sushicore/). Line 53 is 122 characters, not 119.

#### D14. [medium] Agent plans and reports carry absolute paths from one machine

Evidence: Counts of `D:/Projects`, `D:\Projects` or `C:\Users` per file: docs/agent/plans/2026-09-21-terminal-components.md 12, 2026-09-23-provision.md 12, 2026-09-24-module-adoption.md 60, 2026-10-04-standalone-provision.md 43, the untracked 2026-09-25-hub-root-migration.md 16 (line 5 names `C:\Users\sushi\.sushisystems`, line 11 cites the spec as `D:/Projects/sushicore/docs/agent/specs/...`); 16 of the 28 reports also match. The repository is public on GitHub and PyPI (pyproject.toml:28), so these cited paths resolve on no other clone and expose the owner's user name.

Recommendation: When the agent tree is restructured or archived, treat it as one decision with F10/F11: either archive as frozen and accept the paths, or rewrite them repository-relative before the tree moves. Add the rule (repository-relative paths only) to the style guide the skeleton task creates.

Review: found by review.

#### D15. [medium] Work in docs/agent has no matching spec, and some of it belongs to another repository

Evidence: docs/agent/plans/2026-09-24-module-adoption.md (1817 lines) and the untracked 2026-09-25-hub-root-migration.md have no spec of their own; the latter names 2026-09-23-provision-design.md as its spec (line 11) while its goal (line 5) is moving hub's dependency tree, which is sushistack's work. The audit notes that module-adoption plans changes to `st` and `sd` but does not raise the placement: under the documentation skill a work folder holds one SPEC, PLAN and REPORT, and here three plans (provision, module-adoption, hub-root-migration) hang off one spec.

Recommendation: In the restructure, group by piece of work: one unit for the provision programme with its spec and its phase plans, and ask the owner whether cross-repository plans stay in sushicore or move to sushistack/docs/agent, where the sibling wave plans already live.

Review: found by review.

#### D16. [medium] Nothing checks the documentation, so the drift found here will recur

Evidence: The audit records under facts that D:/Projects/sushicore has no tools/ folder, but raises no finding. .github/workflows holds only ci.yml and release.yml; no step checks the layout, link resolution or the changelog shape. The skill's archive step depends on `check_docs_layout.py` listing candidates, and the global CLAUDE.md names `tools/documentation/check_source_comments.py` as the checker every repository carries.

Recommendation: Add the checker set to the skeleton task as a separate brick (tools/documentation/, shaped as in the sibling repositories) and wire it into ci.yml in a later task of its own; this needs owner approval since it adds a top-level folder and a CI step.

Review: found by review.

#### D17. [low] docs/README.md prose needs a register pass

Evidence: D:/Projects/sushicore/docs/README.md has 12 em dashes in 221 lines, most as list-item separators and asides (lines 13, 16, 19, 26, 30, 34, 37, 41, 161, 187). Line 40-41: "most customization needs **no code at all** — just a config file". Line 11: "Small, swappable pieces (SOLID), not one monolith". Lines 5-7: "so a visual change ... is a config edit in one place, not a hunt through three hardcoded `console.py` files" (corrective contrast, and the count of three CLIs is stale against seven in README.md:3). Line 196 bolds "End users".

Recommendation: Fold the pass into the F1 rewrite; the Help screens, Tables and Machine-readable output sections (lines 43-130) already read plainly and can move unchanged.

Review: confirmed. 12 em dashes counted; the quoted phrases are at lines 5-7, 11 and 40-41. Lines 142-143 also carry em dashes inside the TOML sample and are missing from the audit's line list.

#### D18. [low] Document and folder names do not follow UPPER_SNAKE_CASE

Evidence: All 37 files under D:/Projects/sushicore/docs/agent/ are lower-kebab with hyphenated dates, e.g. `docs/agent/specs/2026-09-21-terminal-components-design.md`; the documentation skill requires `UPPER_SNAKE_CASE.md` and `YYYY_MM_DD_UPPER_SNAKE_CASE` work folders.

Recommendation: Rename when the agent tree is restructured under F10, in one commit that also fixes every citation of the old names (specs lines 3, plans, sushistack documents that cite them).

Review: unclear. The names are lower-kebab as stated, and the skill does ask for UPPER_SNAKE_CASE. The global CLAUDE.md names the flat specs|plans|reports layout and its own example files are not shaped by the skill's work-folder rule, so whether this is a defect depends on the layout decision F10 already defers to the owner.

### Not checked

- The 28 files in docs/agent/reports and the 5 plans were not read beyond their first lines, line counts and checkbox counts; their path citations and prose were not checked.
- The three specs were read only at their head and scanned for backticked docs/, sushicore/, tests/ and .github/ paths; bare file names and symbol names cited in them were not resolved.
- Logo width thresholds in docs/README.md:59-62 (72, 68, 20, 16 columns) were not verified; the widths are computed from the pixel grid in sushicore/brand.py and no CLI was run.
- The claim in docs/README.md:19 that Renderer is a Protocol of eight methods: eight methods were confirmed at renderer.py:24-59, but a ninth member `raw` at line 64 was not examined to see whether it is part of the protocol.
- `hub status` states (fetched, linked, sibling, missing) and `hub link sushicore` in docs/README.md:200-208 were not checked against the hub source beyond SUSHICORE_DIR and modules.local.toml.
- Behavioural claims in README.md (setup exits 2 on a missing checkout, doctor --for exits 2 on an unknown group, link pointer precedence under SUSHISTACK_HOME) were not traced through the code; only names, fields and flags were.
- Whether versions 0.5.0, 0.6.0 and 0.7.0 are actually on PyPI was not checked (no network call made); only tags and commits were read.
- Source docstrings and file headers (the source-comments dimension) and the LICENSE text beyond its first lines were not reviewed.
- The contents of .superpowers/sdd/ were listed (first 30 entries) but not read.
- Documents in other repositories that cite sushicore paths (sushistack docs/design, sushistack/cli/README.md beyond the SUSHICORE_DIR hit) were not checked.

## Layout and hygiene

### Facts

- Top-level tree of D:/Projects/sushicore: .git, .github/ (workflows), .gitignore, LICENSE (Apache-2.0 text, 11558 bytes), README.md, pyproject.toml, sushicore/ (the Python package, 85 tracked files), tests/ (83 tracked files), docs/ (38 tracked files), plus three ignored entries: .pytest_cache/ (83K), .superpowers/ (2.4M, 141 files), sushicore.egg-info/ (19K).
- Package subfolders: sushicore/{help,provision,provision/gpu,provision/manifests,provision/packages,provision/toolchains,ui}; tests/{golden,help,provision,ui}. 212 files are tracked in total.
- Declared version: pyproject.toml:7 `version = "0.7.0"` is the only declaration. There is no __version__ in the package, no CMakeLists.txt, no package.json and no sushi-module.toml. sushicore.egg-info/PKG-INFO (generated, ignored) also says 0.7.0.
- Version history in pyproject.toml: 0.5.0 in a5fa5ae (chore(release), 2026-09-23), 0.6.0 inside 7e10c49 (a feat(workspace) commit, 2026-09-24), 0.7.0 in c6d5f55 (chore(release), 2026-10-04).
- Git tags, local and on origin: v0.1.0, v0.2.0, v0.3.0, v0.4.0, all annotated, the last dated 2026-09-22. No v0.5.0, v0.6.0 or v0.7.0 tag exists. 67 commits sit after v0.4.0.
- Remote: origin https://github.com/SushiSystems/SushiCore.git. Only branch is main. Local main is 18 commits ahead of origin/main, 0 behind. HEAD is 9597b64 (2026-10-04).
- Six sibling CLIs pin `sushicore>=0.7.0` (cli/pyproject.toml in sushistack, sushiengine, sushiruntime, sushiai, sushiblas, sushidsp, sushitrack).
- CI workflows: .github/workflows/ci.yml (push to main and pull_request; ubuntu and windows, Python 3.10 and 3.11; `pip install -e .[test]` then `python -m pytest tests -q`) and .github/workflows/release.yml (on `v*` tag: `python -m build`, `twine check`, then publish to PyPI through trusted publishing).
- tools/: the folder does not exist. None of the four checkers (check_source_comments.py, check_docs_layout.py, check_changelog.py, check_layering.py) is present. The reference copies live in D:/Projects/sushiskills/tools/{common,documentation,layering}.
- .gitignore (5 lines): `__pycache__/`, `*.pyc`, `*.egg-info/`, `build/`, `dist/`. .pytest_cache and .superpowers are ignored only by the `*` .gitignore each tool writes inside its own folder.
- git status: one untracked file, docs/agent/plans/2026-09-25-hub-root-migration.md (20901 bytes, an implementation plan). No modified or staged files. Ignored: .pytest_cache/, .superpowers/, sushicore.egg-info/ and 12 __pycache__/ folders.
- Nothing generated or binary is tracked: a scan of git ls-files for images, executables, archives, .pyc, .ini, .log, egg-info, CMake output and dist/ returned no match. The largest tracked file is docs/agent/plans/2026-09-21-terminal-components.md at 122945 bytes; the largest source file is sushicore/provision/steps.py at 36364 bytes.
- docs/ on disk: README.md, CLAUDE.md, reference/CHANGELOG.md, agent/plans (4 tracked + 1 untracked), agent/reports (28), agent/specs (3). No other folder exists under docs/.
- docs/reference/CHANGELOG.md has 56 lines, 51 entries, no `## ` heading of any kind, and no entry over 240 characters.
- Root has no AGENTS.md, CLAUDE.md, .gitattributes or .editorconfig. The only CLAUDE.md is docs/CLAUDE.md.

### Corrections from review

- Fact 7 says 'Six sibling CLIs pin sushicore>=0.7.0' and then lists seven; the count is seven (sushistack, sushiengine, sushiruntime, sushiai, sushiblas, sushidsp, sushitrack cli/pyproject.toml). F1's title already says seven.
- F2 says c6d5f55 is followed by 'five later provision fixes'. Six commits follow it: four fix(provision) (ed10ffe, 197e373, 02d8093, 9597b64), one feat(provision) (fa99b78) and one docs(plan) (c92b329).
- F7 says the scope prefix (`provision:` / `config:`) is on lines 6-17 only; line 24 of docs/reference/CHANGELOG.md carries one as well (13 prefixed entries, not 12).
- F13 calls the two tests/golden files 'byte-compared'. tests/ui/test_logo.py:152 and :157 read them with read_text(encoding='utf-8'), which normalises newlines; they are text-compared. Both are currently LF in index and working tree.
- not_checked says PyPI was not queried. Queried now: https://pypi.org/pypi/sushicore/json reports latest 0.4.0 and releases 0.1.0, 0.2.0, 0.3.0, 0.4.0. No 0.5.0, 0.6.0 or 0.7.0 exists on the index.
- Recomputed and correct: 212 tracked files (sushicore 85, tests 83, docs 38, .github 2); tags v0.1.0-v0.4.0 all annotated; origin/main...HEAD = 0 18; v0.4.0..HEAD = 67; changelog 56 lines / 51 entries / 0 over 240 chars; .superpowers 141 files, 2.4M.

### Findings

#### L1. [high] Versions 0.5.0, 0.6.0 and 0.7.0 were never tagged, and seven CLIs depend on the untagged 0.7.0

Evidence: D:/Projects/sushicore/pyproject.toml:7 says `version = "0.7.0"`. `git tag -l` and `git ls-remote --tags origin` both list only v0.1.0 to v0.4.0. Commits a5fa5ae and c6d5f55 are named `chore(release): prepare sushicore 0.5.0` / `0.7.0` but carry no tag; 67 commits follow v0.4.0. Dependents pin `sushicore>=0.7.0`, e.g. D:/Projects/sushistack/cli/pyproject.toml:17 and D:/Projects/sushiengine/cli/pyproject.toml:15. .github/workflows/release.yml publishes only on a `v*` tag, so nothing after 0.4.0 can have been published by it.

Recommendation: Owner decides which commits become v0.5.0, v0.6.0 and v0.7.0 (or only v0.7.0), then annotated tags are cut per `versioning-and-release`. Until then the `>=0.7.0` pins resolve only against a local checkout.

Review: confirmed. git tag -l and for-each-ref show only v0.1.0..v0.4.0 (annotated); pyproject.toml:7 is 0.7.0; 67 commits after v0.4.0; seven cli/pyproject.toml files pin sushicore>=0.7.0. I also queried PyPI: latest is 0.4.0, releases 0.1.0-0.4.0 only, so the audit's unverified inference holds.

#### L2. [high] 18 commits on main exist only on this machine

Evidence: `git rev-list --left-right --count origin/main...HEAD` returns `0 18`. HEAD is 9597b64 (2026-10-04); the range includes c6d5f55 `chore(release): prepare sushicore 0.7.0` and five later provision fixes.

Recommendation: Push main once the owner approves; this is the only copy of the 0.7.0 work.

Review: confirmed. git rev-list --left-right --count origin/main...HEAD = 0 18; HEAD 9597b64, origin/main 9c0fce1 (2026-09-24). Detail wrong: after c6d5f55 come six commits (4 fix, 1 feat, 1 docs), not 'five provision fixes'.

#### L3. [high] No tools/ folder; none of the four mandatory checkers

Evidence: D:/Projects/sushicore/tools does not exist (`git ls-files tools` is empty). `project-tools` requires tools/documentation/check_source_comments.py, check_docs_layout.py, check_changelog.py and tools/layering/check_layering.py in every repository. The reference set is at D:/Projects/sushiskills/tools/.

Recommendation: Add tools/ with the four checkers and tools/common/ in the shape sushiskills carries.

Review: confirmed. D:/Projects/sushicore/tools absent, git ls-files tools = 0; project-tools requires the four checkers. Reference set exists at D:/Projects/sushiskills/tools/{common,documentation,layering}.

#### L4. [high] Version 0.7.0 no longer names one tree: a feat and four fixes landed after the release commit without a bump

Evidence: D:/Projects/sushicore/pyproject.toml:7 has said 0.7.0 since c6d5f55 `chore(release): prepare sushicore 0.7.0`. Six commits follow it on main: fa99b78 `feat(provision): list a selection's keys and ignore shared fragments`, fixes ed10ffe, 197e373, 02d8093, 9597b64, and c92b329 docs. `git diff --stat c6d5f55..HEAD` shows four changelog lines added and no version change. Tagging c6d5f55 as v0.7.0 leaves out behaviour the siblings may already use; tagging HEAD breaks the rule that the tag sits on the release commit. The audit's F1 offers only 'which commits become v0.5.0, v0.6.0 and v0.7.0'.

Recommendation: Put this choice to the owner alongside F1: tag c6d5f55 as v0.7.0 and release HEAD as v0.7.1 in a `chore(release): v0.7.1` commit (versioning-and-release: feat before 1.0 is a PATCH), or declare 0.7.0 unreleased and cut it at HEAD. Check whether any sibling relies on fa99b78 before choosing; if one does, its pin must become >=0.7.1.

Review: found by review.

#### L5. [medium] Untracked plan that two tracked documents cite

Evidence: D:/Projects/sushicore/docs/agent/plans/2026-09-25-hub-root-migration.md (20901 bytes, dated 2026-09-25) is untracked. docs/agent/plans/2026-10-04-standalone-provision.md and docs/agent/specs/2026-10-04-standalone-provision-design.md both name it. The modules it plans, sushicore/provision/links.py and migrate.py, do not exist, so the plan is still unexecuted intent.

Recommendation: Commit it under docs/agent/plans/, or if the migration was dropped, say so in a status line and commit it to docs/archive/. Either way the cited path must resolve in a clean clone.

Review: confirmed. git status shows the plan untracked (20901 bytes); cited at 2026-10-04-standalone-provision.md:1366 and 2026-10-04-standalone-provision-design.md:14; provision/ has no links.py or migrate.py. The spec says the migration 'runs after this work', so the plan is live and belongs in docs/agent/plans; the archive branch of the recommendation does not apply.

#### L6. [medium] CI runs no checker, calls pytest and pip directly, and the workflow is misnamed

Evidence: D:/Projects/sushicore/.github/workflows/ci.yml:22-25 runs `pip install -e ".[test]"` and `python -m pytest tests -q`. `continuous-integration` requires the four checkers on every push, workflow files named after the trigger (`push.yml`), a dependency cache keyed on the manifest hash, and the command printed as the job's first line. None of these is present.

Recommendation: Rename ci.yml to push.yml, add the checker job once F4 lands, add a pip cache keyed on pyproject.toml. sushicore has no CLI of its own, so the 'CLI only' rule needs an owner ruling for this repository (a tools/ entry point is the obvious stand-in).

Review: confirmed. ci.yml:21-24 runs pip install and python -m pytest directly, no checker job, no cache, no printed command; continuous-integration names push.yml. Note every sibling with CI also uses ci.yml, so the rename is a stack-wide ruling, not a sushicore-only fix. pyproject.toml has no [project.scripts], so 'no CLI of its own' is correct.

#### L7. [medium] release.yml publishes without running tests or checkers, on Linux only

Evidence: D:/Projects/sushicore/.github/workflows/release.yml:9-23 builds with `python -m build` and `twine check` on ubuntu-latest and goes straight to `pypa/gh-action-pypi-publish`. `continuous-integration` says a tag push runs everything the push trigger runs, on Windows and Linux, and then the packaging build.

Recommendation: Make the publish job depend on the full test matrix and the checkers.

Review: confirmed. release.yml:8-38 has only build (ubuntu, python -m build, twine check) and publish; no test or checker job, no Windows leg.

#### L8. [medium] Changelog has no Unreleased or version sections and is not in date order

Evidence: D:/Projects/sushicore/docs/reference/CHANGELOG.md has no `## ` heading (grep for `^## ` is empty), so 0.5.0, 0.6.0 and 0.7.0 cannot be told apart. Line 6 onward runs 2026-10-04 (12), 09-24 (7), 09-23 (2), then one 09-21 entry above five 09-22 entries, then 17 of 09-21, then seven more of 09-22, against the file's own line 3 `newest first`. Entries are also shaped two ways: lines 6-17 carry a `provision:` / `config:` scope prefix, the rest do not.

Recommendation: Add `## Unreleased` and one `## vX.Y.Z — date` section per release, move old sections to docs/archive/changelog/, sort by date, and settle one entry shape.

Review: confirmed. Recomputed: 56 lines, 51 entries, only heading is '# Changelog', 0 lines over 240 chars, date runs 12/7/2/1/5/17/7 exactly as stated. Scope prefix is on lines 6-17 and also line 24, which the audit missed.

#### L9. [medium] The documentation skeleton is mostly absent

Evidence: Under D:/Projects/sushicore/docs only README.md, CLAUDE.md, reference/CHANGELOG.md and agent/ exist. Missing: docs/CONTRIBUTING.md, docs/DOCUMENTATION_STYLE_GUIDE.md, docs/getting_started/, architecture/, modules/, guides/, docs/reference/GLOSSARY.md, KNOWN_ISSUES.md, docs/design/ with REMAINING_WORK.md, docs/archive/. No package folder carries a README (the only tracked READMEs are README.md and docs/README.md), although sushicore/provision, sushicore/ui and sushicore/help are distinct modules.

Recommendation: Build the skeleton as its own approved task. docs/README.md is currently a full manual page, not an index; its content belongs under docs/modules/ or docs/guides/.

Review: confirmed. git ls-files docs gives docs/ (2), agent/plans (4), agent/reports (28), agent/specs (3), reference (1); no CONTRIBUTING, style guide, design/, archive/, GLOSSARY, KNOWN_ISSUES; no README under sushicore/. docs/README.md is a 220-line manual page.

#### L10. [medium] CLAUDE.md sits in docs/, is stale, and the root has no agent instruction file

Evidence: D:/Projects/sushicore/docs/CLAUDE.md is the only one; `repository-layout` puts AGENTS.md and CLAUDE.md in the root. Its line 7 tells the reader to follow `sushiruntime's docs/CONTRIBUTING.md` and line 8 names `docs/slop/` and `docs/api/`, neither of which exists in this repository.

Recommendation: Move it to the root, add AGENTS.md naming the skills the repository follows, and remove the references copied from sushiruntime.

Review: confirmed. docs/CLAUDE.md is the only one; lines 7-8 cite sushiruntime's CONTRIBUTING, docs/slop/ and docs/api/. The audit understates it: line 41 tells the agent to build through `se build` / `se editor`, which this library has no use for, and line 49 is a personal sign-off.

#### L11. [medium] README and manual contradict each other on how sushicore is installed, and the manual cites a missing spec

Evidence: D:/Projects/sushicore/README.md:8-10 says `pip install sushicore`. D:/Projects/sushicore/docs/README.md, section Installing, says `sushicore is not published to any package index`. release.yml publishes to PyPI. docs/README.md also cites `docs/agent/specs/2026-09-05-hub-design.md`, which is not in this repository (the three specs present are dated 09-21, 09-23 and 10-04). docs/README.md's opening lists three CLIs (`sr`, `se`, `hub`); README.md lists seven.

Recommendation: State one install story, fix or qualify the spec path (it appears to be a sushistack document), and bring the CLI list in line.

Review: confirmed. README.md:8-10 `pip install sushicore`; docs/README.md:192 'not published to any package index'; docs/README.md:132 cites docs/agent/specs/2026-09-05-hub-design.md, absent here; docs/README.md:4 lists three CLIs against seven in README.md:3. PyPI does carry sushicore up to 0.4.0, so docs/README.md:192 is false and README's command installs a version no sibling accepts.

#### L12. [medium] README.md is a manual page, not a front door, and duplicates docs/README.md

Evidence: D:/Projects/sushicore/README.md is 84 lines; lines 24-82 document `sushicore.provision` in full (ModuleProvision fields, setup flags, doctor groups, link/unlink behaviour). repository-layout gives the root README three jobs: what the project is, one build line, a link to docs/README.md. The audit's F8 flags docs/README.md for the same fault and F10 the contradiction between the two, but not that the root README carries the provisioning manual.

Recommendation: Move README.md:24-82 into the manual (docs/modules/ once F8's skeleton exists, or sushicore/provision/README.md as that module's own facts) and leave the root README with the description, the install line and the link. One home per fact removes the contradiction F10 reports at its source.

Review: found by review.

#### L13. [medium] tests/ does not follow the yardstick's test tree, and golden data sits outside a fixtures folder

Evidence: `git ls-files tests` gives 28 files flat in tests/, plus tests/help (5), tests/provision (38), tests/ui (10) and tests/golden (2). repository-layout specifies tests/{unit,integration,regression,common}/ for a one-module repository and tests/<kind>/fixtures/ for test data. The audit's F14 raises the Python-library exception for pyproject.toml and the flat package but does not mention tests/.

Recommendation: Fold this into the owner ruling F14 asks for: either the Python-library exception records 'tests mirror the package tree, golden data under tests/golden' as the sanctioned shape, or tests move to tests/unit/... with tests/unit/fixtures/. Do not move files before the ruling.

Review: found by review.

#### L14. [medium] docs/CLAUDE.md instructs agents to build with another product's CLI

Evidence: D:/Projects/sushicore/docs/CLAUDE.md:41 says all builds go through 'this project's dedicated CLI tools - e.g. `se build`, `se editor`'. sushicore has no CLI (pyproject.toml has no [project.scripts]) and is tested with pytest. F9 lists lines 7-8 as the stale part and recommends removing 'the references copied from sushiruntime', which would leave line 41 in place. Line 49 is a personal sign-off that does not belong in an instruction file.

Recommendation: When F9 moves the file to the root, rewrite the Building section to state how this repository is actually verified (the pytest command, and the checkers once F4 lands) and drop line 49. This also settles the 'CLI only' question F5 leaves open, in one place.

Review: found by review.

#### L15. [low] 2.4 MB of agent leftovers in .superpowers/

Evidence: D:/Projects/sushicore/.superpowers/sdd/2026-09-23-provision/ holds 141 files: 43 review `.diff` files, 72 `.md` reports, 18 `.txt` captures, and probe scripts under probe/ (add_docstrings.py, inject_docstrings.py, scan_docstrings.py, probe.py, x.lock), plus commit-task.sh. It is ignored only by .superpowers/sdd/.gitignore (`*`), not by the repository's own .gitignore. The folder is larger than .git (1.8M).

Recommendation: Owner decides whether any report belongs in docs/agent/reports; delete the rest. I did not read the reports, so I cannot say whether they duplicate the 28 already tracked.

Review: confirmed. 141 files, 2.4M against .git 1.8M; 43 .diff, 72 .md, 18 .txt, 4 .py, x.lock, commit-task.sh; probe/ holds the named scripts; ignored only by .superpowers/sdd/.gitignore.

#### L16. [low] .gitignore relies on tools to ignore themselves and misses common Python artefacts

Evidence: D:/Projects/sushicore/.gitignore has five rules. `.pytest_cache/` and `.superpowers/` are ignored only by the nested `*` files those tools write. No rule covers `.venv/`, `venv/`, `.coverage`, `htmlcov/`, `.mypy_cache/`, `.ruff_cache/`, `*.local.toml`, editor folders or `.claude/`.

Recommendation: Add explicit rules for these, so a tool that stops writing its own ignore file cannot leak into a commit.

Review: confirmed. .gitignore has exactly the five rules listed; none for .pytest_cache, .superpowers, venvs, coverage or *.local.toml.

#### L17. [low] Root is missing .gitattributes and .editorconfig

Evidence: `ls -a D:/Projects/sushicore` shows neither file. `repository-layout` lists both in the root. The repository is developed on Windows and tested on Linux, and tests/golden/logo_dark_truecolor.txt and logo_light_truecolor.txt are byte-compared golden files, so line-ending normalisation is not cosmetic here.

Recommendation: Add .gitattributes (`* text=auto eol=lf`, golden files marked explicitly) and .editorconfig matching the sibling repositories.

Review: confirmed. Neither file exists in the root. The supporting argument is overstated: tests/ui/test_logo.py:152,157 read the golden files with read_text (universal newlines), not bytes, so CRLF checkout would not break them. Still real: core.autocrlf=true here and 113 of 212 tracked files sit CRLF in the working tree with nothing pinning eol. 'Matching the sibling repositories' has no single target: only sushiengine and sushiai carry .editorconfig, only sushiruntime, sushidsp, sushitrack carry .gitattributes.

#### L18. [low] Root layout departs from the yardstick: pyproject.toml in the root, flat package

Evidence: D:/Projects/sushicore/pyproject.toml is in the root; `repository-layout` lists `pyproject.toml` as forbidden there, because in the sibling repositories it lives under cli/. Here the repository is itself the Python package (pyproject.toml:35-37 finds `sushicore*` from `.`), so the rule as written has no home to offer. The same shape leaves the generated sushicore.egg-info/ in the root after `pip install -e .`.

Recommendation: Owner ruling needed: either record a Python-library exception in `repository-layout`, or move to a `src/sushicore` layout. This is a module-boundary decision, not one to take silently.

Review: confirmed. pyproject.toml is in the root and lines 35-37 find sushicore* from '.'; repository-layout forbids pyproject.toml in the root. Asking the owner is the right shape for a boundary decision (SOLID item: the recommendation does not pick a boundary silently).

#### L19. [low] The 0.6.0 version bump was made inside a feature commit

Evidence: `git log -G'^version = ' -- pyproject.toml` shows 7e10c49 `feat(workspace): follow a module-side link pointer to the linked workspace` (2026-09-24) changing the version, between the two `chore(release)` commits. `versioning-and-release` step 5 says the version changes in a commit of its own, `chore(release): vX.Y.Z`. The two release commits are also named `prepare sushicore 0.5.0`, not `v0.5.0`.

Recommendation: No history rewrite. From the next release on, bump only in `chore(release): vX.Y.Z` and tag that commit.

Review: confirmed. git log -G'^version = ' -- pyproject.toml lists 7e10c49 feat(workspace) between a5fa5ae and c6d5f55; subjects are 'prepare sushicore 0.5.0/0.7.0', not 'chore(release): vX.Y.Z'.

#### L20. [low] Remote and README use `SushiCore`; folder, package and distribution use `sushicore`

Evidence: origin is https://github.com/SushiSystems/SushiCore.git and README.md:1 is `# SushiCore`, while pyproject.toml:6 is `name = "sushicore"`, docs/README.md:1 is `# sushicore`, and the local folder is D:/Projects/sushicore.

Recommendation: Pick one casing for the product name across the README title, the manual title and the forge name, in line with whatever the sibling repositories settle on.

Review: unclear. The casing difference exists (origin SushiSystems/SushiCore.git, README.md:1 'SushiCore', pyproject name 'sushicore'), but siblings follow the same convention (SushiEngine.git, SushiAI.git, SushiDSP.git): CamelCase product and forge name, lowercase package. The only inconsistency inside the repository is docs/README.md:1 '# sushicore' against README.md:1. As a remote-name mismatch it is not a defect.

### Not checked

- Whether sushicore 0.5.0, 0.6.0 or 0.7.0 is on PyPI; I did not query the index, so F1's 'cannot have been published by release.yml' rests on the missing tags only.
- The CI run history on GitHub (whether main is green).
- The contents of the 141 files under .superpowers/, beyond their names and sizes.
- Source comment and docstring conformance of sushicore/ and tests/ (the source-comments dimension); only the head of sushicore/__init__.py was seen.
- License headers in source files.
- Internal layering between sushicore/ subpackages (what check_layering.py would report).
- Link and cited-path resolution across docs/agent/ plans, reports and specs, apart from the two paths named in F3 and F10.
- Status lines and archive candidates in docs/agent/ (28 reports from 2026-09-21/22 may be closed work that belongs in docs/archive/).
- Line endings and encoding of tracked files; whether tests/golden files are stored LF or CRLF.
- The .github/ folder beyond workflows/ (it holds only the two tracked workflow files).
- Git history for large or binary blobs that were committed and later removed.
- The sibling repositories' own layouts in depth; only their root listings, tools/ and workflow file names were read for comparison.
- The yardstick skills were loaded; `documentation`, `commits` and `source-comments` were not, so findings F7 and F8 rest on the global CLAUDE.md wording.

## Code shape

### Facts

- Languages: Python only. 212 tracked files: 164 .py, 39 .md, 2 .yml, 2 .toml, 2 .txt, LICENSE, py.typed, .gitignore. No C++, GLSL or TypeScript, so cpp-code-style and typescript-code-style do not apply.
- One distributable package (pyproject.toml, name sushicore, version 0.7.0, license Apache-2.0, requires-python >=3.10). Runtime deps: rich, tomli (<3.11); optional typer; click is imported under TYPE_CHECKING in typer_help.py.
- Internal modules (tracked .py files / lines): sushicore root 27 / 3369; sushicore/ui 9 / 472; sushicore/help 5 / 232; sushicore/provision root 17 / 3192; provision/gpu 10 / 1259; provision/packages 8 / 916; provision/toolchains 6 / 691; provision/manifests 1 / 15 (+ base.deps.toml). Source total 87 files / 10146 lines.
- Tests (files / lines): tests root 28 / 2926; tests/ui 10 / 664; tests/help 5 / 534; tests/provision 38 / 5239; plus tests/golden with two logo text goldens. 77 .py files, 9363 lines, 726 test functions. Run in CI with `python -m pytest tests -q` on ubuntu and windows, Python 3.10 and 3.11 (.github/workflows/ci.yml).
- Dependency direction, presentation side: ui -> theme, brand, markup; help -> ui, theme; typer_help -> help, ui, console; console -> renderer, theme, icons; renderer -> events, theme, ui (lazy), windows_console (lazy); __init__ -> config, console, icons, renderer, terminal_background, theme, typer_theme.
- Dependency direction, config/build side: config_base -> workspace; workspace -> config_base (lazy, inside functions); module_config -> config_base, profile, workspace; diag -> profile, workspace; cmake_driver -> cmake_cache; stack_config -> provision.home, provision.config.
- Dependency direction, provision: commands -> steps -> {packages, toolchains, gpu, probe, sinks, selection, pipeline}; gpu -> probe, system, toolchains.stamp, sushicore.build_env; packages -> system, probe, gpu.registry; toolchains -> packages, stamp; provision -> root (profile, workspace, config_base, deps_fragment, build_env). Root stack_config imports provision, so root and provision depend on each other.
- Twenty largest .py files (lines): provision/steps.py 820; tests/provision/test_toolchain_installers.py 632; tests/provision/test_adapter_builder.py 516; tests/provision/test_commands.py 467; provision/probe.py 457; tests/provision/test_windows_cuda_install.py 426; tests/test_typer_help.py 386; provision/gpu/adapter_builder.py 357; provision/commands.py 340; provision/toolchains/adaptivecpp.py 324; workspace.py 312; renderer.py 312; tests/help/test_from_click.py 275; tests/provision/test_gpu_backend_specs.py 268; provision/packages/linux.py 257; tests/test_cmake_driver.py 249; provision/gpu/cuda.py 241; build_env.py 240; provision/packages/direct_download.py 235; provision/gpu/windows_installer.py 223.
- Test layout: one flat tests/ tree with subfolders ui, help, provision that mirror the package; no unit/integration/regression/benchmark split. tests/test_ui_architecture.py enforces the ui/ shape (one class per file, allowed imports) by AST; no equivalent exists for any other module.
- Source files with no test file and no test that references them by name: sushicore/diag.py, sushicore/typer_theme.py, provision/packages/base.py, provision/packages/linux.py, provision/packages/winget.py, provision/toolchains/_process.py. Files with no own test file but referenced from other tests: cli_console.py, config_base.py, icons.py, help/model.py, provision/fragments.py, gpu/level_zero.py, gpu/rocm.py, packages/github_release.py, toolchains/adaptivecpp.py, intel_llvm.py, oneapi.py.
- There is no tools/ directory, so tools/documentation/check_source_comments.py and every other checker the skills assume are absent.
- License headers: all 42 files under sushicore/provision carry a two-line `# Copyright ... / # Licensed under the Apache License` header; the 41 files in sushicore root, ui and help carry none. No file uses the boxed license block from source-comments, and none names an author.
- AST scan of the 87 source files: 39 functions/classes without a docstring, 32 docstrings longer than 8 lines, 19 module docstrings longer than 6 lines (config.py is 26), 50 unannotated parameters/returns, 25 dataclasses that are not frozen+slots, 20 files with more than one top-level class, 10 uses of @final (all in ui/ and help/), 35 K_-prefixed module constants against 31 without the prefix.
- Logging: one stdlib logger in the whole package (typer_help.py:27, K_LOGGER = logging.getLogger("sushicore.help"), used with %s arguments). Everything else reports through the Console facade, which is user-facing output and not a log. No f-string log calls were found.
- Module verdicts: ui - sound. help - sound. provision/gpu - needs targeted fixes. provision/packages - needs targeted fixes. provision/toolchains - needs restructuring. provision root (steps, probe, commands, pipeline, system) - needs restructuring. sushicore root (presentation + config + build driver) - needs targeted fixes. tests - needs targeted fixes.

### Corrections from review

- Facts, test layout: 'no equivalent [of tests/test_ui_architecture.py] exists for any other module' is wrong. D:/Projects/sushicore/tests/provision/test_layering.py holds a layer table for every provision module and asserts imports point downward and never reach sushihub. F4's recommendation should extend that test to the root package, not start a new one.
- Facts and F17: 'no test references them by name' is wrong for provision/packages/linux.py, provision/packages/winget.py and provision/toolchains/_process.py. They are named in tests/provision/test_packages_api.py:12-13, test_commands.py:17, test_install_deps_gpu.py:10 and test_layering.py. Corrected statement: only sushicore/diag.py and sushicore/typer_theme.py have no reference at all; the other four have no behavioural test.
- F4 title 'import cycles between the root package and provision': there is no module-level cycle. stack_config imports provision, provision imports config_base, workspace, profile, deps_fragment and build_env, and none of those imports stack_config or provision. The only real cycle is workspace.py <-> config_base.py. build_env.py imports nothing from sushicore, so the deferred import at gpu/adapter_builder.py:74 (cited as 75) avoids no cycle.
- F4: gpu/cuda.py:14 and packages/direct_download.py:18 importing probe are not layering violations; test_layering.py places probe at layer 1, gpu at 2 and packages at 3.
- F5: provision/lock.py:75 and 106 do not swallow; both re-raise after closing or unlocking the descriptor.
- F12 and facts: module docstrings over six lines number 16 by stripped line count (config.py 25), not 19 (config.py 26). proc.py, icons.py and console.py sit at exactly the limit under that count.
- F20: `_SHOW_PROGRESS` is used (commands.py:220) and patched by tests/provision/test_commands.py:65; it is not dead code.
- F9 line numbers: Rich tables are printed at diag.py:128 and 170 and discovery.py:132; the cited 113, 147 and 118-119 are the import lines.
- F11: provision/fragments.py:22 `Dependency(FragmentDependency)` subclasses deps_fragment.Dependency; the audit lists the two as unrelated same-named classes.
- Recomputed and correct: 212 tracked files (164 .py), per-module file and line counts, the twenty largest files, 726 test functions, 19 broad-except sites, 37 subprocess calls in 18 files, 42/41 licence-header split, 39 missing docstrings, 32 long docstrings, 50 unannotated, 25 dataclasses, 20 multi-class files, 10 @final, 35 K_ constants, version 0.7.0, no tools/ directory.

### Findings

#### C1. [high] provision/steps.py holds four step classes and several unrelated responsibilities in 820 lines

Evidence: D:/Projects/sushicore/sushicore/provision/steps.py: DetectStep (158), InstallDepsStep (376), ConfigureStep (627), UninstallStep (669) in one file. DetectStep both probes the machine and prints the table and advice (run, 330-361; _report_inventory, 363). InstallDepsStep carries the Linux routine (427-514), the Windows routine (516-542), a hard-coded winget command for VS Build Tools (606-613) and the toolchain install (400-425). `_manager` is copied verbatim at 387-392 and 681-686; the Linux manager list appears three times (87, 429, 698); three near-identical remove blocks at 744-764.

Recommendation: Split to one step per file under provision/steps/, move the manager lookup into one shared brick that owns the Linux-manager list, separate inventory collection from its rendering, and move the VS Build Tools install behind the package-manager contract. The module wave should start here.

Review: confirmed. Read sushicore/provision/steps.py: classes at 158, 376, 627, 669; _manager identical at 387-392 and 681-686; Linux manager list at 87, 429, 698; three remove blocks at 744-764; winget argv at 606-613. All as cited.

#### C2. [high] Platform and package-manager kinds are switched on by name instead of dispatched through the existing contracts

Evidence: steps.py:97 (`if platform == "windows"`), 396-398 and 690-692 (`_run_windows` / `_run_linux`), 487-510 (`mgr.name == "apt"` decides oneAPI and GPU install), 443 and 704 (`assert isinstance(mgr, LinuxPackageManager)`), 92 (`m.name == "vcpkg"`). probe.py:367-369 (`_resolve_windows` / `_resolve_linux`), 315, 333. commands.py:101-106 (`_managers_for` lists every manager class). 51 platform checks across 15 files, 13 of them in provision/gpu/adapter_builder.py. gpu/backend.py:66 (PlatformLocator) already shows the table-driven shape the rest does not use.

Recommendation: Give install and uninstall a per-platform strategy object registered in a table (as PlatformLocator does), and let IPackageManager answer capability questions (`can_install_oneapi`, `translate`) so a new platform or manager adds a file rather than editing steps.py, probe.py and commands.py.

Review: confirmed. steps.py:92, 97, 396, 443, 487, 499, 690, 704, probe.py:367-369, commands.py:101-106 and gpu/backend.py:66 all match. My grep gives 54 platform checks in 18 files (13 in adapter_builder.py) against the audit's 51 in 15; the pattern differs, the conclusion does not. SOLID note: `can_install_oneapi` on IPackageManager would put toolchain knowledge into the package-manager contract; the toolchain spec should name the managers it supports.

#### C3. [high] The shared core hard-codes its consumers' names and commands

Evidence: steps.py:155 (`"hub install" if ctx.program == "hub"`), 216 and 293 (owner literal "sushiruntime" decides whether the SYCL row exists), 344, 422-424 (`hub install --customize`). pipeline.py:53 (`program: str = "hub"` default). toolchains/intel_llvm.py:47-48 and 90 (`sr build --type asan`, `hub install --refresh-toolchains`). toolchains/adaptivecpp.py:261 (`sr setup --profile normal`). The dependency is supposed to point from hub/sr down to sushicore.

Recommendation: Carry the rerun command, the refresh command and the SYCL-owner flag in InstallContext or ModuleProfile, supplied by the consuming CLI. Remove every `program == "hub"` branch and every literal product name from provision.

Review: confirmed. steps.py:155, 216, 293, 344, 422; pipeline.py:53; intel_llvm.py:47-48, 90; adaptivecpp.py:261 all present. One more site the audit did not list: adaptivecpp.py:252 (`sr setup acpp`).

#### C4. [high] Import cycles between the root package and provision, and between workspace and config_base

Evidence: sushicore/stack_config.py:20-21 imports `.provision.home` and `.provision.config`; provision imports root in the other direction: provision/config.py (`from ..config_base`), provision/home.py (`from ..workspace`), provision/commands.py:11-12 (`..profile`, `..workspace`), provision/fragments.py (`sushicore.deps_fragment`), gpu/adapter_builder.py:75 (`from sushicore.build_env import ...`, deferred to dodge the cycle). workspace.py:148 and 165 import `.config_base` inside functions while config_base.py:21 imports `.workspace` at module level. gpu/cuda.py:14 imports `..probe`, and packages/direct_download.py:18 imports `..probe` while steps and probe sit above packages.

Recommendation: Fix the tier order in writing (foundation: workspace, config_base, proc, build_env; presentation; provision; then stack_config on top or inside provision) and move write_toml_document below workspace. Owner decision: this is a module boundary. Add an import-direction test like tests/test_ui_architecture.py for the whole package.

Review: unclear. Half holds. workspace.py:148/165 <-> config_base.py:21 is a real cycle hidden by lazy imports, and root and provision depend on each other as packages (stack_config.py:20-21 down, provision/config.py:10, home.py:11, commands.py:11-12, sinks.py:11-12 up). But no module-level cycle exists there: nothing provision imports reaches stack_config. build_env.py imports no sushicore module, so the deferred import at adapter_builder.py:74 (not 75) dodges no cycle. gpu/cuda.py and packages/direct_download.py importing probe is a downward import under tests/provision/test_layering.py (probe 1, gpu 2, packages 3), not a violation.

#### C5. [high] Failures are swallowed with no return status and no record

Evidence: provision/packages/base.py:93-94 (`except Exception: pass` around the whole PATH refresh). provision/packages/direct_download.py:55-56 (`except Exception: pass` around the registry PATH write, so a failed persistent PATH edit is silent). provision/probe.py:275, 291, 305 (`except Exception: return ""/False`). build_env.py:143-145 (cache write failure dropped). provision/system.py:39-41, gpu/cuda.py:220-222, gpu/adapter_builder.py:330-333, renderer.py:74-77. provision/lock.py:75 and 106 catch BaseException. 19 `except Exception`/`BaseException` sites in total.

Recommendation: Narrow each to the exceptions the call can raise (OSError, subprocess.SubprocessError) and either return a status the caller reports or emit one console.warn naming the operation, the value and the consequence. The two registry sites are the priority because the user is told the install succeeded.

Review: confirmed. 19 broad-except sites recomputed and match. base.py:93-94 and direct_download.py:55-56 are `except Exception: pass` as cited; probe.py:275, 291, 305 return ''/False. Two corrections: lock.py:75 and 106 catch BaseException, release the handle and re-raise, so they swallow nothing; build_env.py:143-145, system.py:39-41, cuda.py:220-222, adapter_builder.py:330-333 and renderer.py:74-77 are already narrow (`except OSError`/ValueError) and only lack a record.

#### C6. [high] Downloaded archives and installers are extracted and executed with no integrity check

Evidence: D:/Projects/sushicore/sushicore/provision/packages/direct_download.py:28-35 streams a URL to disk and 96 and 148 call `zf.extractall(stage)` on it with no hash and no member-path check. sushicore/provision/toolchains/oneapi.py:59-61 returns an existing `~/intel-oneapi-toolkit-offline.exe` if the file merely exists, so a curl run that was interrupted leaves a partial 4 GB file that the next run executes; 63 downloads with curl and checks only the exit code. sushicore/provision/toolchains/intel_llvm.py:108-110 falls back to an unfiltered `tf.extractall` when the `filter` argument is missing, which is the case on older 3.10 and 3.11 patch releases the package supports. The only verification in the package is MD5 in gpu/windows_installer.py:91-98. A grep for sha256/checksum in sushicore/ finds nothing else.

Recommendation: One download brick that takes url, destination and expected digest, writes to `<file>.part`, verifies and renames (gpu/windows_installer.py HttpDownloader already has this shape). Route direct_download, intel_llvm and oneapi through it. Owner decision: where pinned digests live (the deps fragment is the likely home) and whether unpinned 'latest' assets stay allowed.

Review: found by review.

#### C7. [medium] No module base error; steps and installers signal failure by bool, None and bare built-in exceptions

Evidence: Only four exception classes exist and none shares a base: provision/lock.py:24 `LockTimeout(Exception)`, provision/registry.py:43 `RegistryError(Exception)`, typer_help.py:33, workspace.py:190 `LinkEditError(ValueError)`. Bare built-ins raised: packages/github_release.py:23, 41, 53 (RuntimeError), provision/_output.py:29, deps_fragment.py:95, closure.py:49, selection.py:80, fragments.py:194, events.py:26, icons.py:43, theme.py:109. module_config.py:75 raises SystemExit from library code, and build_env.py:195-197 and cli_console.py:58-61 catch SystemExit as control flow. Callers then catch `Exception` because nothing narrower exists (toolchains/intel_llvm.py:61, 78; adaptivecpp.py:120, 136; gpu/provisioning.py:41). steps.py:569 returns `tuple[list[str], bool | None]` with None as a third state.

Recommendation: Define SushicoreError and one base per module (ProvisionError, WorkspaceError), raise specific subclasses, replace the SystemExit raise with a NotAProjectError that the entry point converts, and replace the tri-state bool with an enum or a result type.

Review: confirmed. Four exception classes with no shared base (lock.py:24, registry.py:43, typer_help.py:33, workspace.py:190). Bare built-in raises at every cited line. module_config.py:75 raises SystemExit; it is caught at build_env.py:196, cli_console.py:60 and also module_config.py:100, which the audit did not list. steps.py:569 returns bool | None.

#### C8. [medium] Four copies of the subprocess runner and 37 direct subprocess calls beside sushicore.proc.Runner

Evidence: The same Popen-and-stream loop exists at sushicore/proc.py:121-140 (run_drained), provision/packages/base.py:17-33 (run), provision/gpu/adapter_builder.py:49-62 (SubprocessCommandRunner.run), and a fourth variant at provision/toolchains/_process.py:12-34 (_run_quiet). 37 `subprocess.run/Popen` calls across 18 files, e.g. steps.py:61 and 619, system.py:49 and 69, toolchains/oneapi.py:63, 89, 105. Only gpu/adapter_builder.py:37 has an injectable CommandRunner protocol.

Recommendation: Keep one runner brick (proc.Runner or the CommandRunner protocol) and inject it into package managers, toolchain installers and steps. This also removes the need for monkeypatching subprocess in tests.

Review: confirmed. Recomputed 37 subprocess.run/Popen calls in 18 files. The four runner copies exist: proc.py:122-134, packages/base.py:17-33, gpu/adapter_builder.py:49-62, toolchains/_process.py:12-34. Recommendation is brick-shaped.

#### C9. [medium] Duplicated probe tables and helpers across provision

Evidence: `_NVCC_GLOBS_LINUX` defined twice: provision/probe.py:37-40 and provision/gpu/cuda.py:31-34. Windows SDK rc.exe globs twice: probe.py:32-35 and toolchains/adaptivecpp.py:85-88. CMake Program Files paths twice: probe.py:403-405 and packages/direct_download.py:70-74. `clang++.exe if windows else clang++` written 8 times (probe.py:133, 162, 338, 342; gpu/provisioning.py:22; toolchains/intel_llvm.py:37; stack_config.py:111, 124). Download-extract-move recipe repeated in direct_download.py:81-110 and 132-162. Pass-through wrappers: direct_download.py:24 tools_dir, probe.py:112 and 117, toolchains/stamp.py:17 all forward to provision/home.py:82-87. TOML read duplicated: config.py:55 `_read_toml` and workspace.py:42 `read_toml`; the tomllib/tomli fallback import is repeated in config.py:38, deps_fragment.py:24, workspace.py:21, provision/registry.py:13. `_APT_TO_DNF` and `_APT_TO_ZYPPER` (packages/linux.py:14, 34) differ in two entries.

Recommendation: One install-locations brick that owns the well-known paths and the compiler executable name; one archive-install helper for the portable tools; one TOML reader in the foundation. Delete the pass-through wrappers and import home directly.

Review: confirmed. _NVCC_GLOBS_LINUX at probe.py:37 and gpu/cuda.py:31; rc.exe globs at probe.py:33-34 and adaptivecpp.py:86-87; CMake paths at probe.py:404-405 and direct_download.py:71-72; 8 clang++.exe sites; 4 tomllib fallbacks; _APT_TO_DNF and _APT_TO_ZYPPER differ in exactly ninja-build and libgtest-dev. SOLID note: an 'install-locations brick' that owns both the well-known paths and the compiler executable name holds two responsibilities; they should be two bricks.

#### C10. [medium] Rich leaks through the public Console surface, and provision bypasses the Renderer seam

Evidence: sushicore/renderer.py:63-66 puts an untyped `raw` property returning a Rich Console on the Renderer protocol; console.py:37-40 re-exposes it as `Console.console`. Ten call sites in provision use it: pipeline.py:130 (Rich Progress built inline, 121-152), steps.py:614 and 648, toolchains/oneapi.py:83, adaptivecpp.py:60-77, packages/base.py:29, gpu/adapter_builder.py:60, toolchains/_process.py:33. With JsonRenderer, `raw` is a stderr console (renderer.py:262-267), so this output never becomes an event. steps.py:13 and probe.py:179 import rich.markup.escape directly, and probe.py returns pre-escaped Rich markup from a probing function. ui/component.py:7 puts rich's RenderableType in the Component protocol (accepted by the ui design, but it is the public type). diag.py:113, 147 and discovery.py:118-119 build Rich tables directly.

Recommendation: Add the missing semantic calls (status/spinner, raw child output line, literal text) to Renderer and Console, route the ten sites through them, and keep Rich types inside renderer.py and ui/. Owner decision on whether `Console.console` stays public.

Review: confirmed. renderer.py:63-66 untyped `raw`, console.py:37-40 `Console.console`, 10 call sites in provision recomputed, JsonRenderer.raw at 262-267 writes to stderr. Line corrections: the Rich prints in diag.py are at 128 and 170 and in discovery.py at 132 (the cited lines are the imports). Root also uses it at proc.py:132 and typer_help.py:98.

#### C11. [medium] Global mutable console in provision, and type checks standing in for a contract

Evidence: provision/_output.py:8-34: module-level `_provider` set by `bind_console`, read through a `_ConsoleProxy.__getattr__` singleton imported by about 30 provision files; python-code-style forbids module-level singletons and hidden globals. provision/commands.py:275, 285, 302, 323 must call bind_console in every command. console.py:57-59 answers `is_machine` with `isinstance(self._renderer, JsonRenderer)`. renderer.py:239-248 recovers the level by searching the icon prefix text for 'info/success/warn/error', which returns 'info' for every level under the 'emoji', 'minimal' and 'none' icon sets (icons.py:27-30). cli_console.py:21-27 keeps a hand-written `_ATTRS` list of Console methods that must be edited for each new method.

Recommendation: Pass the console into steps, managers and installers through their constructors. Pass the level to Renderer.line explicitly and let the renderer declare whether it is a machine renderer. Derive the lazy-console attribute set from Console.

Review: confirmed. _output.py:8-34, bind_console at commands.py:275, 285, 302, 323, console.py:57-59, cli_console.py:21-27 all as cited. The level defect is real and is a behaviour bug, not shape: console.py:63-75 passes the icon as prefix and renderer.py:276 derives the level from it, so every JSON line event reads level=info under the emoji, minimal and none icon sets. It deserves its own high-severity finding with a regression test. A second hidden global the audit missed: provision/home.py:27 (`global _bound`).

#### C12. [medium] Siblings shaped differently: toolchains are free functions, GPU backends are specs behind a protocol

Evidence: provision/gpu has a contract and a registry (gpu/backend.py:31 ToolkitLocator, 99 GpuBackendSpec; gpu/registry.py:51 BACKENDS). provision/toolchains has none: intel_llvm.install_intel_llvm(cfg, dry_run, refresh) -> str|None, adaptivecpp.install_adaptivecpp(cfg, mgr, vcpkg, dry_run, assume_yes) -> str|None, oneapi.install_oneapi(ctx) -> bool, called one by one from steps.py:404-417 and 540, with matching boolean fields on pipeline.py:25-32 ToolchainSelection and a third table in selection.py:26-32 COMPONENTS and a fourth in probe.py:181-185. toolchains/__init__.py re-exports nothing. Root package: old files (theme.py, icons.py, config.py, build_env.py, cmake_driver.py) use plain dataclasses and untyped params, new ones (ui/, help/) use @final frozen slots dataclasses. Two unrelated classes named Component (provision/registry.py:23, provision/selection.py:15) and a third in ui/component.py:13; two named Registry (provision/registry.py:52, gpu/registry.py:13); two named Dependency (deps_fragment.py:48, provision/fragments.py:22).

Recommendation: Give toolchains the same shape as GPU backends: a ToolchainSpec with key, label, probe and installer, registered in one table that selection, probe and the install step all read. Rename the colliding classes. Adding a toolchain today edits five files.

Review: confirmed. Toolchain installers are free functions with three different signatures and return types (intel_llvm.py:24, adaptivecpp.py:148, oneapi.py:28); gpu has ToolkitLocator and a registry. ToolchainSelection at pipeline.py:25-32 and COMPONENTS at selection.py:27-33 as cited. Correction: provision/fragments.py:22 Dependency subclasses deps_fragment.Dependency, so those two are related, not a name collision. The three Component and two Registry classes are unrelated as stated.

#### C13. [medium] File openings do not follow the source-comments rule, and differ between halves of the package

Evidence: 42 files under sushicore/provision open with a two-line `# Copyright` header (e.g. provision/steps.py:1-2); 41 files in sushicore root, ui/ and help/ have no license block at all (e.g. sushicore/renderer.py:1, sushicore/console.py:1, sushicore/ui/panel.py:1). No file states an author. 19 module docstrings exceed six lines: config.py (26), profile.py (17), module_config.py (15), deps_fragment.py (14), cli_console.py (14), discovery.py (13), diag.py (13), __init__.py (13), stack_config.py (12), config_base.py (12), build_env.py (12), workspace.py (11), typer_theme.py (10), renderer.py (10), cmake_driver.py (9), toolchain_args.py (8), proc.py, icons.py, console.py (7). provision/__init__.py lacks `from __future__ import annotations`.

Recommendation: Apply one header to all 87 files once the licence is decided (the header text changes in that wave anyway), and move the long module docstrings into docs/architecture or docs/design, leaving a one-sentence summary and a path.

Review: confirmed. Recomputed: 42 files under provision open with `# Copyright`, the other 41 with none; no author anywhere; provision/__init__.py is the only file without the __future__ import. My count of module docstrings over six lines is 16 (config.py 25) against the audit's 19 (config.py 26); the audit counted the closing line. The conclusion holds either way.

#### C14. [medium] Docstrings carry design rationale and history, 39 symbols have none, and 32 exceed eight lines

Evidence: History and rationale in source: cli_console.py:9-13 ("Four of the five CLIs had found that out... sushiengine's copy never received the fix"), build_env.py:151-154 ("SushiEngine, SushiAI and SushiBLAS each carried a copy of this"), workspace.py:5-6 ("used to be copy-pasted"), workspace.py:32 ("before 2026-09-22"), profile.py:9 and 91, diag.py:138-140, typer_theme.py:3-9, theme.py:68-73 (six stacked # lines citing D:/Projects/sushiweb/src/styles/global.css, an absolute path on one machine). Missing docstrings (39): icons.py:15, 21, 34, 38, 46; theme.py:104, 112; config.py:46, 55; proc.py:21, 29, 31, 33, 47, 76; provision/checks.py nine nested `fn` at 39-170; diag.py:33-35, 60; build_env.py:164; cmake_driver.py:35. Doxygen `@param/@return` tags inside Python docstrings instead of Google style: build_env.py:156-159, cmake_cache.py:25-27, cmake_driver.py:29-30 and 56, stack_config.py:36 and 49. Longest symbol docstrings: profile.py:58 (15 lines), gpu/backend.py:99 (14), proc.py:54 (14), diag.py:42 (13).

Recommendation: Move the rationale to design documents, convert the @param blocks to Google style, add the missing one-sentence docstrings. The root package is where almost all of this sits; provision, ui and help are mostly clean.

Review: confirmed. Recomputed 39 symbols without a docstring and 32 docstrings over eight lines. History text read at cli_console.py:9-13, build_env.py:151-154, theme.py:68-73 (absolute D:/ path confirmed). The Doxygen-tag list is understated: @param/@return/@raise appear in 11 root files (65 lines), with workspace.py 11, profile.py 10, config_base.py 6, diag.py 5 and proc.py 4 not named by the audit.

#### C15. [medium] Units with more than one responsibility outside steps.py

Evidence: provision/probe.py (457 lines): Visual Studio discovery (64-109), toolchain status with display strings (156-192), GPU vendor classification with marker tables (195-292), binary verification (295), SYCL compiler choice (309-358), config value resolution per platform (361-457). workspace.py (312 lines): walk-up and TOML layering (37-131), module registry writes (133-188), link-block text splicing (190-312). provision/packages/base.py: the IPackageManager contract (97) plus `run`, `prime_sudo` (36) and `refresh_windows_path` (63). provision/system.py: os facts plus the Intel apt repository setup (52-73), which is a package-manager concern re-exported from packages/__init__.py:7. provision/pipeline.py: StepResult, ToolchainSelection, InstallContext, Step and InstallPipeline, with the Rich progress UI inside the runner (121-152). sushicore/__init__.py:56-83 defines build_console and _use_color instead of only re-exporting. 20 files hold more than one top-level class (gpu/windows_installer.py 9, doctor.py 6, packages/linux.py 6).

Recommendation: Split probe.py into vs_locator, gpu_vendor, sycl_compiler and local_config; split workspace.py into workspace lookup, module registry and link editing; move the process helpers out of packages/base.py; move build_console into its own module.

Review: confirmed. probe.py sections sampled at 270-308, 364-370, 444-457; base.py holds run, prime_sudo, refresh_windows_path and IPackageManager; 20 files with more than one top-level class recomputed. The proposed splits are one responsibility each.

#### C16. [medium] Untyped seams on the build side

Evidence: 50 unannotated parameters or returns: cmake_driver.py (11; `def __init__(self, console, runner)` at 35, `cfg` and `env` untyped at 41-145), build_env.py (10; `snapshot_windows(cfg, console)` at 91, `StackBuildEnv.__init__(self, *, profile, console, find_root, ...)` at 164), renderer.py (8; `raw` at 64, `stream=None` at 171 and 254), steps.py:166-167 and 191, windows_console.py (4), diag.py (3), provision/lock.py (3). provision/commands.py:88 types the console provider as `Callable[[], object]` and then calls `.error`, `.success` on it (174, 315). build_env.py:180 reads `getattr(cfg, name + "_dir", "")`, gpu/backend.py:83 reads `getattr(cfg, "platform", None)`. Three separate structural console protocols exist: proc.py:21-33, discovery.py:35-44, and the untyped ones.

Recommendation: Declare one ConsoleLike protocol and one BuildConfig protocol in the foundation and annotate these signatures with them.

Review: confirmed. 50 unannotated parameters/returns recomputed; commands.py:88 `Callable[[], object]` confirmed; renderer.py:64 and 254 untyped. SOLID note: merging the three narrow console protocols into one wide ConsoleLike works against interface segregation; a narrow protocol per consumer, declared in one foundation file, is the brick-shaped fix.

#### C17. [medium] Six source files have no test, and the test tree does not follow the testing layout

Evidence: No test file and no test reference: sushicore/diag.py (config_show, env_dump), sushicore/typer_theme.py, provision/packages/base.py (run, prime_sudo, refresh_windows_path), provision/packages/linux.py (five managers and the apt translation tables), provision/packages/winget.py, provision/toolchains/_process.py. tests/ is flat with ui/help/provision subfolders; tests/regression, tests/integration and tests/benchmark do not exist, although tests/provision/test_commands.py (467 lines) and test_install_deps_gpu.py drive several modules together. Test files are not one per source file: workspace.py is covered by test_workspace_link.py and test_workspace_modules.py, renderer.py by test_json_renderer.py and test_renderer_components.py, config.py by test_appearance_background.py. tests/provision/test_checks.py:71 runs a child `time.sleep(5)` to test a timeout, which is wall-clock dependent.

Recommendation: Add unit tests for the Linux managers' translate_apt and the winget manager behind an injected runner (after F7), and for diag. Decide whether sushicore adopts tests/{unit,integration,regression} or documents the mirror layout as its own.

Review: confirmed. diag.py and typer_theme.py have no reference in tests (grep empty). The 'no test references them by name' claim is wrong for three files: tests/provision/test_packages_api.py:12-13 names AptManager, DnfManager, YumManager, PacmanManager, ZypperManager, WingetManager; LinuxPackageManager is subclassed at test_commands.py:17-21 and test_install_deps_gpu.py:10-24; toolchains._process is a key in test_layering.py. None of those exercises behaviour, so the gap stands. tests/provision/test_checks.py:71 sleep(5) confirmed (timeout patched to 0.1 at line 70).

#### C18. [medium] The package supports Python 3.10 while python-code-style sets 3.11 as the floor

Evidence: D:/Projects/sushicore/pyproject.toml:21 `requires-python = ">=3.10"`, classifiers at 16-17, `tomli` dependency at 24; .github/workflows/ci.yml matrix runs 3.10 and 3.11. The four tomllib/tomli fallback imports (config.py:38-40, deps_fragment.py:24-26, workspace.py:21-23, provision/registry.py:13-15) and the unfiltered tar fallback at toolchains/intel_llvm.py:110 exist only because of that floor. The audit recorded the floor as a fact and the fallbacks as duplication, but not the conflict with the yardstick.

Recommendation: Owner decision: raise the floor to 3.11 (drops tomli and the four fallbacks) or record the 3.10 exception in the repository's own documentation. It is a public-surface change for every consuming CLI, so it goes through api-stability.

Review: found by review.

#### C19. [medium] Tests reach into private names across the suite

Evidence: A grep for `setattr(<module>, "_...` and calls to `._name(` under D:/Projects/sushicore/tests finds about 65 sites, for example tests/provision/test_commands.py:65 (`_SHOW_PROGRESS`), test_commands.py:448 (`_managers_for`), tests/provision/test_checks.py:70 (`_VERSION_TIMEOUT`), tests/provision/test_install_deps_gpu.py:83-87 (private InstallDepsStep methods replaced by lambdas), tests/provision/test_toolchain_installers.py:383 (`_acpp_deps_linux`). The testing skill says private details are not tested directly and that a private function needing a test is a brick that wants its own module. The audit listed test bodies under not_checked, so this was not covered.

Recommendation: Treat each patched private as a missing seam: the manager list, the progress flag and the timeout become constructor arguments of the command or step, and helpers such as `_acpp_deps_linux` become public functions of their own module. This follows from F7 and F10 and should be planned with them.

Review: found by review.

#### C20. [medium] More hidden module state than the one global the audit names

Evidence: D:/Projects/sushicore/sushicore/provision/home.py:27 (`global _bound`, a second process-wide binding beside _output.py:19). sushicore/icons.py:26-35: `_ICON_PRESETS` is a module-level mutable dict that `register_icon_set` writes into. python-code-style forbids module-level singletons and hidden globals; F10 covers only provision/_output.py.

Recommendation: Pass the provision home into the steps and probes through InstallContext or their constructors, and make the icon and theme tables explicit registry objects owned by whoever builds the console. Check sushicore/theme.py for the same registration pattern in the module wave; I did not read it.

Review: found by review.

#### C21. [low] Stacked comment lines and separators

Evidence: Stacked `#` lines beyond the two-line license header: theme.py (13 pairs, 68-73 and others), build_env.py (7, e.g. 204-206), profile.py (5), config_base.py (5), cmake_driver.py (4), discovery.py:116-117, diag.py:138-140, provision/probe.py:169-170, provision/gpu/compiler_identity.py. Over-long single comments: probe.py:36 and 402. Separator lines: tests/provision/test_toolchain_installers.py:22, 24, 98, 100, 231, 233, 444, 446. No TODO, FIXME, HACK or XXX found anywhere, and no commented-out code was seen in the sample.

Recommendation: Collapse each stacked block to one invariant line or move it to a document; split test_toolchain_installers.py (632 lines, four sections) into one test file per installer, which removes the separators.

Review: confirmed. Separator lines confirmed at tests/provision/test_toolchain_installers.py:22-24; theme.py:68-73 stacked block confirmed; no TODO/FIXME found. I did not recount the stacked pairs per file.

#### C22. [low] Class-shape and naming rules applied to ui/ and help/ only

Evidence: @final appears 10 times, all in ui/ and help/ (e.g. ui/panel.py:15, help/model.py:9). 25 dataclasses are not `frozen=True, slots=True`: mutable ones include config.py:46 AppearanceSpec, config_base.py:25 ToolConfig, provision/config.py:39, provision/doctor.py:49 FunctionCheck, provision/gpu/adapter_builder.py:105 AdapterBuilder (a service declared as a dataclass), stack_config.py:25. Module constants without K_: 31, e.g. workspace.py:27 WORKSPACE_MARKER, provision/system.py:12 USER_AGENT, provision/selection.py:27 COMPONENTS, renderer.py:239 _LEVELS, against 35 with it (ui/table.py:24-28, typer_help.py:26-27). Interfaces are ABCs with an I prefix (packages/base.py:97 IPackageManager, fragments.py IDependencySource, pipeline.py:77 Step) where the style asks for typing.Protocol. `assert` used for a runtime type claim at steps.py:443 and 704 and proc.py:130. Package sits at ./sushicore, not source/sushicore as python-code-style lays out.

Recommendation: Mechanical pass once the structural fixes are in. Renaming public constants and IPackageManager is an API change for hub and the module CLIs, so it goes through api-stability and needs the owner's decision.

Review: confirmed. 10 @final (ui/ and help/ only), 35 K_ constants, 25 dataclasses not frozen+slots recomputed. asserts at steps.py:443, 704 and proc.py:130 confirmed. ABC interfaces at packages/base.py:97 confirmed.

#### C23. [low] The one log call and the user-facing warnings do not all answer what, values and next step

Evidence: typer_help.py:86-93 is correct in form (K_LOGGER, %s arguments, names the command, the error and the fallback), but it sits on a blanket `except Exception` and no handler is configured anywhere in the package, so the warning is only seen through logging's last-resort handler. Console messages that name no value or consequence: provision/packages/base.py:32 (`Command failed (N).`), steps.py:621 (`Visual Studio Build Tools install failed or was cancelled.`, exit code dropped), toolchains/oneapi.py:65 and 112 (no exit code), steps.py:370 (`Needs attention`). provision/packages/base.py:124 warns `remove not implemented, skipping` and returns True.

Recommendation: Decide whether sushicore has a log at all (one category per module) or only console output, and state it in the module README. Add the exit code and the consequence to the four messages.

Review: confirmed. typer_help.py:86-93 read; one logger in the package (typer_help.py:27). Messages at base.py:32, steps.py:370, 621, oneapi.py:65, 112 and base.py:124 match.

#### C24. [low] Dead and vestigial code

Evidence: provision/probe.py:448 and 455: `compiler, path = find_sycl_compiler(cfg)` followed by `del path`. provision/commands.py:68-71: `_locate_nothing` takes `name` and deletes it. provision/commands.py:65 `_SHOW_PROGRESS = True`, a constant flag never set elsewhere in the file. steps.py:182-188: DetectStep._dep_manager and _vcpkg_manager only forward to the module functions at 90-99. steps.py:110-115 `_first_available` has no caller in steps.py (callers elsewhere not confirmed). provision/toolchains/__init__.py docstring says 'the provenance stamp' while the package holds three installers. console.py:104-107 keeps two call forms for `table` to serve 'a renderer written before grouping existed', although all three renderers accept group_by.

Recommendation: Confirm each with a repository-wide search in the module wave and delete. `_first_available` and `_SHOW_PROGRESS` need a check against tests and against hub, which may patch them.

Review: confirmed. `_first_available` (steps.py:110) has no caller anywhere in the repository, tests included. probe.py:448/455 and commands.py:68-71 as cited. Correction: `_SHOW_PROGRESS` is not dead; commands.py:220 reads it and tests/provision/test_commands.py:65 patches it, so it is a test seam and belongs under F10 (hidden module state), not under dead code.

### Not checked

- Files not read in full: sushicore/provision/checks.py, closure.py, config.py, doctor.py (only 80-140), fragments.py (only 14-75), home.py, lock.py, registry.py (only 15-60), selection.py (only 10-45), sinks.py; provision/gpu/adapter_builder.py (only 30-75 and 325-336), compiler_identity.py, cuda.py (only 1-80 and 200-241), level_zero.py, rocm.py, windows_installer.py; provision/packages/github_release.py, vcpkg.py, linux.py after line 135; provision/toolchains/adaptivecpp.py (only 50-150 and 255-263), oneapi.py (only 60-115), stamp.py.
- Root files not read beyond their outline: brand.py, cmake_cache.py, cmake_driver.py, config_base.py, deps_fragment.py (only 40-70), discovery.py, events.py, markup.py, module_config.py, proc.py (only 95-150), profile.py, stack_config.py, terminal_background.py, toolchain_args.py, windows_console.py, diag.py.
- ui/: read component.py, panel.py and the head of table.py only; definition_list.py, header.py, logo.py, title.py, usage.py not read. help/: read model.py and logo_choice.py only; from_click.py and page.py not read.
- Test bodies were not reviewed: test naming, assertion quality, float tolerances, fixtures in conftest.py and tests/ui/capture.py, and whether the two goldens under tests/golden are compared byte-for-byte. Only greps for sleep, network and skip were run.
- No test was run and no coverage was measured; 'no test' means no test file and no textual reference, not measured line coverage.
- The cycle between root and provision was read from import statements; it was not confirmed by importing the package, so whether any of it fails at import time is unverified.
- `_first_available`, `_SHOW_PROGRESS` and the other dead-code candidates in F20 were not searched for in the consuming repositories (sushihub, sushiruntime and the other CLIs), which may import or patch them.
- Public API stability: which of the renamed or restructured names in F11 and F18 are imported by hub/sr/se/sa/sb/sd/st was not checked.
- docs/, README.md, LICENSE text, .github/workflows/release.yml and provision/manifests/base.deps.toml content are outside this dimension and were not reviewed.
- Windows versus Linux behaviour (registry writes, sudo, apt repositories) was read, not exercised.
- humanizer register of existing docstrings was not assessed beyond the rationale and history cases in F13.
