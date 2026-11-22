# Command surface

**Describes:** `source/sushicore/provision/commands.py`, `source/sushicore/provision/package_command.py`, `source/sushicore/diag_commands.py`, `source/sushicore/root_options.py`, `source/sushicore/command_groups.py`, `source/sushicore/testing/commands.py`, `source/sushicore/testing/session.py`, `source/sushicore/clean_command.py`, `source/sushicore/run_options.py`, `source/sushicore/command_surface/build_command.py`, `source/sushicore/command_surface/run_command.py`, `source/sushicore/command_surface/bench_command.py`, `source/sushicore/command_surface/check_command.py`

The commands below are the ones this package declares for a CLI. A module's own commands, such
as `sa train`, are declared by the module and are not listed here. `--describe` prints the surface of a
CLI, its own commands included and its hidden ones left out, as one JSON document.

## Exit codes

| Code | Means |
| --- | --- |
| `0` | The command did what it was asked to do |
| `1` | The command ran and failed: a step failed, a check found a fault, a file could not be written |
| `2` | The command could not act on the request: an unknown group, an unknown toolchain, no workspace, a path that is not a workspace, a missing module |
| `127` | `package` found no cmake or CPack |

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
| `setup` | `--dry-run`, `--yes` or `-y`, `--toolchain` (repeatable), `--no-gpu`, `--accept-licences` | Provisions what the module needs to build, then runs `doctor` |
| `doctor` | `--for GROUP` | Reports the checks of the module; `GROUP` is `build`, `test`, `infer`, `eval` or a group the module adds, and every check of the group is required. Exits `1` when a required check fails |
| `link` | `--workspace PATH` | Records the module in a workspace, which must carry its marker, as one operation |
| `unlink` | `--workspace PATH` | Removes the module's entry and its link |
| `package` | `--build-dir`, `--prefix`, `--no-archive`, `--force` | Installs a built tree to a prefix and archives it with CPack |

## Tests

`test` is declared once by `register_test_command`, for a CLI whose tests run under CTest.

| Command | Options | Does |
| --- | --- | --- |
| `test` | `--label` or `-l` (repeatable), `--filter` or `-f`, `--repeat` or `-r`, `--jobs` or `-j` (used exactly as given; when absent, the `build_jobs` key of `[tool]` in the config, else the hardware threads less four, at least one, as a ceiling that the run lowers to fit the free memory at 256 MB per `small` test or 1024 MB per `medium` or `large` one, and prints the count), `--all`, `--shuffle/--no-shuffle`, `--seed N`, `--sanitize NAME`, `--cli` | Runs the tests of the build tree, `small` and `medium` unless a label is named, with CTest writing a JUnit file, in a shuffled order whose seed it prints, then prints the budget line |

`--label quarantined` alone runs the quarantined tests and no size. `--label large` without `--filter` exits
`2` before anything runs; `--all` adds every size and lifts that rule. A tree that is absent, or that the
module reports as faulty, also exits `2`.

`--sanitize` builds the tree of that sanitizer and tests it; the run is not judged by the time limits and prints no budget line, because a sanitizer slows every test several times and its oracle is its report. A CLI that builds a sanitizer tree of its own, such as `sr test --type asan`, passes `time_limits=False` to `run_tests` for the same reason. `--cli` runs the pytest suite of the CLI itself for the
labels and nothing else: it starts no CTest, writes no JUnit file, prints no budget line and checks neither the
large rule nor the tree, and it exits `2` when given `--filter`, `--repeat`, `--jobs`, `--all` or `--sanitize`. A CLI
shows an option only when it has what the option needs. Using a hidden one exits `2`, and a sanitizer the CLI does
not build exits `2` and names the ones it does, or `none`.

The shuffle is on unless `--no-shuffle` is given. The seed is `--seed`, or a random one from 1 to 99999 that the
command prints; it reaches the GoogleTest programs as `GTEST_SHUFFLE` and `GTEST_RANDOM_SEED`, which CTest passes on
to each test. `--cli` does not shuffle. A module whose CTest call neither names `shuffle_seed` nor takes `**keywords` runs in the
given order, and the command warns.

A build can register the cases of a program in shards, CTest tests named `<program>.<size>_shard_<i>of<N>`, or `<program>.<size>_quarantined`, that each
write GoogleTest XML to `test_results/gtest/<name>.xml` in the tree. The command empties that folder before a run, and
the budget reader gets it as `--cases` when the run left files there. Over such a build `--filter` is a GoogleTest
filter, and CTest cannot narrow a shard that names its own `--gtest_filter`, which GoogleTest ranks above the
variable. A module that hands the command a `run_program` has the command run the selected shards itself: it reads each
shard's program, size filter, `GTEST_TOTAL_SHARDS` and `GTEST_SHARD_INDEX`, labels and timeout from the tree's
`CTestTestfile.cmake` files and runs the program with `--gtest_filter` set to the cases the shard's filter and `--filter`
both select (the shard's negative patterns and the filter's are kept; a shard that can hold no such case is not run),
the shard's variables and timeout, `--jobs` shards at once, and `--gtest_output=xml:` into `test_results/gtest/<name>.xml`.
The exit codes of the shards go into the JUnit file, so the rerun and the budget line work as for a CTest run. An
unfiltered run stays on CTest. A module with no `run_program` gets the filter as `GTEST_FILTER`, which a shard that names
its own filter overrides, and one whose CTest call neither names `gtest_filter` nor takes `**keywords` keeps the `-R`
pattern, and the command warns.

A failed CTest test is rerun once, alone, after the run and before the budget line; a pass on the rerun is reported
flaky, and the exit code stays CTest's. A failed shard reruns only its failing cases, read from its XML, by
`--gtest_filter` on its program, through the `run_program` the module hands the command, into `test_results/rerun`,
which the reader gets as `--rerun`. Any other failed test, and a shard whose cases cannot be read or whose module has no
`run_program`, reruns whole by `ctest -R` into a JUnit file of its own.

The budget line comes from `test_budget.py`, in the testing folder of the shared tools below the module's root, and is printed only when
the repository carries it. The JUnit file is `junit.xml` in the tree's `Testing` folder; a run that wrote none prints
a warning instead. The reader first lists the tests over a limit, which run again alone, one at a time, into
`test_results/slow`; it then judges each by its time alone. When CTest passed, a broken limit ends the run with exit
code 1, and a reader that cannot judge the run, such as one older than the CLI, with 2; when CTest failed, the code
stays CTest's. A run the module does not report as current (a sanitizer run always is) ends its line with
"(not rebuilt)" and never gates; the repository's budget exemption file, `budget_exemptions.toml` in its tests folder
when present, is handed to the reader.

CTest gets `resources.json` in the tree's `Testing` folder as its resource file: one `gpus` slot, the accelerator the
machines that run the tests carry, so the shards that declare `RESOURCE_GROUPS gpus:1` run one at a time. A filtered run
over shards runs the shards that need an accelerator one after another for the same reason, and the others `--jobs` at
once.

## Cleaning and running

`clean` is declared once by `register_clean_command`, and the options of a `run` command by `run_options`.

| Command | Options | Does |
| --- | --- | --- |
| `clean` | `--type` or `-t` (repeatable), `--sanitize` (repeatable), `--all`, the extra flag a CLI names, `--yes` or `-y` | Lists the build trees the selection holds and removes them only with `--yes`; without it nothing is removed and the exit code is `2`. `--all` selects the whole build folder and takes no `--type` or `--sanitize` |
| `run` | `--type` or `-t`, `--pick`, `--all` | `--type` runs from the tree of that type. `--pick` offers the built examples to choose from, and `--all` with it also lists the test and benchmark programs. `--sort`, the old spelling of `--pick`, is hidden and names its replacement |

## Building, running, benchmarks and checks

`build`, `run`, `bench` and `check` are declared by `register_build_command`, `register_run_command`,
`register_bench_command` and `register_check_command` in `command_surface`. Their flags, and the verbs
and panels every CLI shares, are in [Command line interface](../guides/COMMAND_LINE_INTERFACE.md). A
value the shared flags refuse, such as a build type the CLI does not build or `--sanitize
address,thread`, exits `2` before the CLI's service runs; otherwise the exit code is the service's.

## Diagnostics

| Command | Options | Does |
| --- | --- | --- |
| `config` | none | Prints every resolved setting and the file it came from |
| `env` | `--all` or `-a` | Prints the environment build processes run under, the build-relevant part unless `--all` |

## Groups

`backlog` and `design` are named once in `command_groups`, and a test checks a CLI carries them with
`missing_groups`. `docs bundle` is declared by `docs_bundle/commands.py`.

| Group or command | Does | Reference |
| --- | --- | --- |
| `backlog` | Reads and changes the backlog; `check` exits `1` on a finding | [Backlog](BACKLOG.md) |
| `design` | Reads and changes the design topics; `check` exits `1` on a finding | [Design topics](DESIGN.md) |
| `sync`, `check` | Copies the shared tools from a SushiCore tag and checks them against the lock; `register_shared_tools_commands` adds them to an app, and `python -m sushicore.shared_tools` runs them with no CLI | [Shared tools](SHARED_TOOLS.md) |
| `docs bundle` | Bundles the published documentation for a release | [Documentation bundle](DOCS_BUNDLE.md) |
