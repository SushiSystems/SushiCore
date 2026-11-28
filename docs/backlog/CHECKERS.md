# Checkers

## Remaining work

| ID | Pri | State | Title | Done when | Blocked by | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RW-179 | P2 | open | Check that every symbol carries a `@brief` | `check_source_comments.py` reports a C++ symbol without `@brief` |  | `source/sushicore/tools/documentation/check_source_comments.py` | 2026-11-28 |
| RW-180 | P2 | open | Read Python imports across modules in the layering check | `check_layering.py` reports a Python import that crosses a module boundary the layering forbids |  | `source/sushicore/tools/layering/check_layering.py` | 2026-11-28 |
| RW-181 | P2 | open | Check that a changelog entry's verb is past tense | `check_changelog.py` reports an entry whose verb is not in the past tense |  | `source/sushicore/tools/documentation/check_changelog.py` | 2026-11-28 |
| RW-182 | P2 | open | Check that changelog entries run newest first | `check_changelog.py` reports an entry dated after the one above it |  | `source/sushicore/tools/documentation/check_changelog.py` | 2026-11-28 |
| RW-183 | P2 | open | Resolve links outside `docs/` | `rule_links` checks the root README, module READMEs and paths cited in backticks |  | `source/sushicore/tools/documentation/check_docs_layout.py` | 2026-11-28 |
| RW-184 | P2 | open | Check module READMEs in every layout | `rule_module_readmes` checks a single-module repository and a skills repository |  | `source/sushicore/tools/documentation/check_docs_layout.py` | 2026-11-28 |
| RW-185 | P2 | open | Check the licence block of shell and CMake files | `rule_license_block` reads `.sh` and `.cmake` files |  | `source/sushicore/tools/documentation/check_source_comments.py` | 2026-11-28 |
| RW-186 | P2 | open | Tell a second personal copyright line from an upstream notice | `rule_license_block` reports a second copyright line that is not an upstream notice |  | `source/sushicore/tools/documentation/check_source_comments.py` | 2026-11-28 |
| RW-187 | P2 | open | Read reference-style links and links around an image | `rule_links` and `rule_reachable_from_index` follow both kinds |  | `source/sushicore/tools/documentation/check_docs_layout.py` | 2026-11-28 |
| RW-188 | P2 | open | Refuse a changelog without its title and `## Unreleased` | `check_changelog.py` reports a `CHANGELOG.md` that lacks `# Changelog` or `## Unreleased` |  | `source/sushicore/tools/documentation/check_changelog.py` | 2026-11-28 |
| RW-189 | P2 | open | Let the test mirror checker skip listed units | `check_test_mirror.py` skips the units `tools/settings.py` lists and fails on a listed unit that gained a test; SushiDSP's `untested_units.txt` is gone |  | `source/sushicore/tools/testing/check_test_mirror.py` | 2026-11-28 |
| RW-190 | P2 | open | Read TypeScript imports in the layering check | `check_layering.py` reports a TypeScript import that crosses a boundary the repository's tier order forbids |  | `source/sushicore/tools/layering/check_layering.py` | 2026-11-28 |
| RW-191 | P2 | open | Read C# in the comment, licence and layering checks | `check_source_comments.py` and `write_license_block.py` read `.cs` files, and `check_layering.py` reads a Unity tree's assembly definitions |  | `source/sushicore/tools/documentation/check_source_comments.py` | 2026-11-28 |
| RW-192 | P2 | open | Write bulk edits through a temporary file and the changelog as fragments | a tool that rewrites many files refuses to shrink one past a set share and copies it first, and an entry is added as a file beside the changelog and joined at… |  |  | 2026-11-28 |
| RW-193 | P2 | open | Check a built phase against a test and make a shipped design shrink | a phase marked built may name an existing test or command that a checker verifies, and a shipped design above a set size is a finding |  | `source/sushicore/design/` | 2026-11-28 |
| RW-194 | P1 | open | Split the checkers into a pure core and a file-walking shell so their tests are small | every checker's rules pass the purity run, each test file keeps the shell in at most one medium class, and no mutant survives on the changed lines |  | `source/sushicore/tools/` | 2026-11-28 |
| RW-195 | P2 | open | Report gtest_discover_tests in a build file that gives no reason for it | a shared checker reports each such call after a base commit, with tests |  | `source/sushicore/tools/testing/` | 2026-11-28 |
| RW-196 | P2 | open | Give design_status a pure status parser that check_docs_layout reuses | check_docs_layout keeps no copy of the design listing or status parse, and design_status reads no disk in its parser |  | `source/sushicore/tools/documentation/design_status.py` | 2026-11-28 |
| RW-197 | P3 | open | Move check_all's plan into its own module so known_findings needs no lazy import | known_findings.py and check_all.py both import the plan module and neither imports the other |  | `source/sushicore/tools/checking/known_findings.py` | 2026-11-28 |
| RW-198 | P2 | open | Make mutate_diff remove its temporary tree on Windows and print its totals | a run on Windows leaves no mutate_diff_* folder and always ends with the mutants line |  | `source/sushicore/tools/testing/mutate_diff.py` | 2026-11-28 |
| RW-199 | P2 | open | Make mutate_diff mutate the lines of files the diff adds | a file added after the base and not yet committed has its lines mutated |  | `source/sushicore/tools/testing/mutate_diff.py` | 2026-11-28 |
| RW-200 | P1 | open | Stop mutate_diff from leaving test process chains behind | a stopped or finished run leaves no python process of its temporary tree, and each mutant runs only the tests that import the file |  | `source/sushicore/tools/testing/mutate_diff.py` | 2026-11-28 |
| RW-201 | P2 | open | Find a test that makes a device, queue or runtime outside its module's one fixture base | check_test_value.py reports a test source that constructs a device, queue or runtime outside the fixture base, as testing's Running fast rule 3 says |  | `source/sushicore/tools/testing/check_test_value.py` | 2026-11-28 |
| RW-202 | P2 | open | Judge a row name by the table the name generator reads, not by the file | check_test_odr passes a SCOPED_TRACE-only table in a file whose generator reads another table's name |  | `source/sushicore/tools/testing/check_test_odr.py` | 2026-11-28 |
| RW-203 | P2 | open | Run the shared checkers' mutation sample in each release of SushiCore | the release step of SushiCore runs a mutation sample and records its survivors |  |  | 2026-11-28 |
| RW-204 | P2 | open | Read cited paths under tools/build in check_docs_truth | check_docs_truth reports a missing path cited under tools/build in a test tree |  | `source/sushicore/tools/documentation/check_docs_truth.py` | 2026-11-28 |
| RW-205 | P2 | open | Make check_test_mirror finish inside a minute on SushiEngine's tree | check_test_mirror runs on SushiEngine's tree in under 60 s, measured on the dev machine |  | `source/sushicore/tools/testing/check_test_mirror.py` | 2026-11-28 |
| RW-206 | P3 | open | Give check_test_mirror a scoped mode for one module and its tests | check_test_mirror takes a module path and reports findings for that module and its tests only |  | `source/sushicore/tools/testing/check_test_mirror.py` | 2026-11-28 |
| RW-207 | P2 | open | Let pre-commit check the index while other files stay unstaged | a commit whose staged files pass is admitted while another tracked file differs on disk, shown by a test |  | `source/sushicore/tools/hooks/pre_commit.py` | 2026-11-28 |

## Known issues

| ID | Origin | Symptom | Workaround | Fix | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- |
