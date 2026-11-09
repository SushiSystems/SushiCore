# Command surface

**Describes:** `source/sushicore/provision/commands.py`, `source/sushicore/provision/package_command.py`, `source/sushicore/diag_commands.py`, `source/sushicore/root_options.py`, `source/sushicore/command_groups.py`, `source/sushicore/testing/commands.py`, `source/sushicore/testing/session.py`

Every command line built on this package answers to the commands below. A module's own commands, such
as `build` and `test`, are declared by the module and are not listed here. `--describe` prints the
whole surface of a CLI, its own commands included, as one JSON document.

## Exit codes

| Code | Means |
| --- | --- |
| `0` | The command did what it was asked to do |
| `1` | The command ran and failed: a step failed, a check found a fault, a file could not be written |
| `2` | The command could not act on the request: an unknown group, an unknown toolchain, no workspace, a path that is not a workspace, a missing module |

`setup`, `link`, `unlink` and `doctor` end with one `result` event in machine mode, whatever their code, except
`doctor` with a `--for` group it does not know, which exits `2` without one. `package` emits no `result` event; its
exit code is the installer's.

## Before any command

| Option | Does |
| --- | --- |
| `--version` | Prints the version of the CLI and exits `0` |
| `--describe` | Prints the catalogue of commands, options and groups as JSON and exits `0` |

## Provisioning

`setup`, `doctor`, `link` and `unlink` are declared once by `register_provision_commands`, and `package` by
`register_package_command`. A binary install carries `doctor` alone.

| Command | Options | Does |
| --- | --- | --- |
| `setup` | `--dry-run`, `--yes` or `-y`, `--toolchain` (repeatable), `--no-gpu` | Provisions what the module needs to build, then runs `doctor` |
| `doctor` | `--for GROUP` | Reports the checks of the module; `GROUP` is `build`, `test`, `infer`, `eval` or a group the module adds. Exits `1` when a required check fails |
| `link` | `--workspace PATH` | Records the module in a workspace, which must carry its marker, as one operation |
| `unlink` | `--workspace PATH` | Removes the module's entry and its link |
| `package` | `--build-dir`, `--prefix`, `--no-archive`, `--force` | Installs a built tree to a prefix and archives it with CPack |

## Tests

`test` is declared once by `register_test_command`, for a CLI whose tests run under CTest.

| Command | Options | Does |
| --- | --- | --- |
| `test` | `--label` or `-l` (repeatable), `--filter` or `-f`, `--repeat` or `-r`, `--jobs` or `-j` (one per core, lowered to fit the free memory at 256 MB per `small` test or 1024 MB per `medium` or `large` one, when absent; the count is printed), `--all`, `--shuffle/--no-shuffle`, `--seed N`, `--sanitize NAME`, `--cli` | Runs the tests of the build tree, `small` and `medium` unless a label is named, with CTest writing a JUnit file, in a shuffled order whose seed it prints, then prints the budget line |

`--label quarantined` alone runs the quarantined tests and no size. `--label large` without `--filter` exits
`2` before anything runs; `--all` adds every size and lifts that rule. A tree that is absent, or that the
module reports as faulty, also exits `2`.

`--sanitize` builds the tree of that sanitizer and tests it. `--cli` runs the pytest suite of the CLI itself for the
labels and nothing else: it starts no CTest, writes no JUnit file, prints no budget line and checks neither the
large rule nor the tree, and it exits `2` when given `--filter`, `--repeat`, `--jobs`, `--all` or `--sanitize`. A CLI
shows an option only when it has what the option needs. Using a hidden one exits `2`, and a sanitizer the CLI does
not build exits `2` and names the ones it does, or `none`.

The shuffle is on unless `--no-shuffle` is given. The seed is `--seed`, or a random one from 1 to 99999 that the
command prints; it reaches the GoogleTest programs as `GTEST_SHUFFLE` and `GTEST_RANDOM_SEED`, which CTest passes on
to each test. `--cli` does not shuffle. A module whose CTest call neither names `shuffle_seed` nor takes `**keywords` runs in the
given order, and the command warns.

A build can register the cases of a program in shards, CTest tests named `<program>.<size>_shard_<i>of<N>` that each
write GoogleTest XML to `test_results/gtest/<name>.xml` in the tree. The command empties that folder before a run, and
the budget reader gets it as `--cases` when the run left files there. Over such a build `--filter` is a GoogleTest
filter: it reaches every shard as `GTEST_FILTER` and not as `ctest -R`, and a shard whose command line names its own
`--gtest_filter` keeps that one, which GoogleTest ranks above the variable. A module whose CTest call neither names
`gtest_filter` nor takes `**keywords` keeps the `-R` pattern, and the command warns.

A failed CTest test is rerun once, alone, after the run and before the budget line; a pass on the rerun is reported
flaky, and the exit code stays CTest's. A failed shard reruns only its failing cases, read from its XML, by
`--gtest_filter` on its program, through the `run_program` the module hands the command, into `test_results/rerun`,
which the reader gets as `--rerun`. Any other failed test, and a shard whose cases cannot be read or whose module has no
`run_program`, reruns whole by `ctest -R` into a JUnit file of its own. The reader judges only the tests that were
rerun, so an over-limit case that did not fail is not listed in a run that failed.

The budget line comes from `test_budget.py`, in the testing folder of the shared tools below the module's root, and is printed only when
the repository carries it. The JUnit file is `junit.xml` in the tree's `Testing` folder; a run that wrote none prints
a warning instead. The line is a report and never changes the exit code, which is CTest's. A run the module does
not report as rebuilt (a sanitizer run always is) ends its line with "(not rebuilt)" and never gates; the repository's
budget exemption file, `budget_exemptions.toml` in its tests folder when present, is handed to the reader.

## Diagnostics

| Command | Options | Does |
| --- | --- | --- |
| `config` | none | Prints every resolved setting and the file it came from |
| `env` | `--all` or `-a` | Prints the environment build processes run under, the build-relevant part unless `--all` |

## Groups

`backlog` and `design` are named once in `command_groups`, and a test checks a CLI carries them with
`missing_groups`. `docs bundle` is declared by `docs_bundle/commands.py`.

| Group | Does | Reference |
| --- | --- | --- |
| `backlog` | Reads and changes the backlog; `check` exits `1` on a finding | [Backlog](BACKLOG.md) |
| `design` | Reads and changes the design topics; `check` exits `1` on a finding | [Design topics](DESIGN.md) |
| `docs bundle` | Bundles the published documentation for a release | [Documentation bundle](DOCS_BUNDLE.md) |
