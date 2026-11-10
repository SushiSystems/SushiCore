# sushicore.testing

The `test` command every Sushi CLI with CTest tests registers, and the pieces it is built from. The
rules it carries out are the `testing` skill's: a default of `small` and `medium`, no `large` run
without a filter, and one budget line after every CTest run, which fails a passing run of a current tree
that breaks a time limit. Its options are in
[Command surface](../../docs/reference/COMMAND_SURFACE.md).

## What it owns

| Name | File | Does |
| --- | --- | --- |
| `TestLabel`, `LabelSelection`, `select_labels`, `large_needs_a_filter` | `labels.py` | Name the labels `--label` accepts, turn them into the `ctest -L` and `-LE` patterns, and say when a run would start the `large` tests unfiltered |
| `scope_of`, `reader_command`, `program_map`, `judge_run` | `budget.py` | Decide what a run is judged as, build the calls of the budget reader, map each suite to its program, rerun alone what is over a limit and return the gate's code |
| `SlowTestRerun` | `slow_rerun.py` | Rerun alone, one at a time, the tests a run found over their time limit: a shard's cases through its program, any other test through CTest with one job |
| `resource_spec_text`, `resource_spec_file`, `write_resource_spec`, `K_ACCELERATORS` | `accelerator_slots.py` | Write the CTest resource file that gives each accelerator one slot, so shards declaring `RESOURCE_GROUPS gpus:1` never share one |
| `ModuleTests`, `SanitizedTests`, `TestConsole` | `module_tests.py` | What one module CLI hands the command: its tree, its CTest call, its checkout and its console, and the sanitizer builds and the pytest suite it may add |
| `choose_jobs`, `JobChoice`, `share_of` | `job_count.py` | Pick the job count of a run given none: one per core, lowered so the jobs' memory shares fit the free memory, a `small` run at 256 MB per test and any other at 1024 MB, and the line that prints it |
| `registers_shards`, `program_of`, `program_executable`, `gtest_results_folder`, `rerun_results_folder`, `slow_results_folder` | `shards.py` | Tell whether a build registers its cases as shards, name the program of a shard, find the executable its shards run and name the folders a run leaves their results in |
| `ProgramRunner`, `run_with_timeout` | `program_runner.py` | Run a test program of a tree by the name its shards carry, under the module's environment, with variables and a timeout when given; a CLI hands it to `ModuleTests` as `run_program` |
| `intersect_filters` | `gtest_filter.py` | Join a shard's GoogleTest filter and the caller's into the filter that selects the cases both select |
| `ShardRegistration`, `shard_registrations` | `shard_registrations.py` | Read each shard's program, size filter, variables, labels, timeout and whether it declares `RESOURCE_GROUPS` from the tree's CTest test files |
| `junit_text` | `junit_report.py` | Write the JUnit file of a run the command made itself |
| `run_filtered_shards` | `filtered_run.py` | Run the selected shards under the caller's case filter through `run_program`, at most `--jobs` at once, the shards that need an accelerator one after another |
| `failed_tests`, `failing_cases`, `case_names`, `ResultFileError` | `result_files.py` | Read the failed CTest tests from the JUnit file, and the failing and all `Suite.Case` names from a shard's GoogleTest XML |
| `FailedTestRerun`, `RerunOutcome` | `rerun.py` | Rerun the failed tests once, alone: a failed shard's failing cases by `--gtest_filter` on its program, any other test by `ctest -R`; tell flaky from failing |
| `run_tests` | `session.py` | Refuse a run that cannot start, build a sanitizer tree when asked, empty the shard results, run CTest with a JUnit file and the resource file, rerun what failed and judge the run by its time limits, or hand the labels to the CLI's own pytest suite |
| `register_test_command` | `commands.py` | Add `test` to a Typer application |
| `label_option`, `filter_option`, `repeat_option`, `jobs_option`, `all_option`, `shuffle_option`, `seed_option` | `options.py` | Declare the options of `test`, once, for the command here and for a CLI that keeps a command of its own |

The package re-exports `register_test_command`, `ModuleTests`, `SanitizedTests`, `TestLabel`, `LabelSelection`,
`select_labels`, `run_tests` and the seven option functions; the other names are the package's own and no CLI imports them.

## What it depends on

Inside sushicore, only `sushicore.profile`; Typer is imported when the command is registered. A module
supplies its CTest call, so the package imports no build driver.

The budget reader is `test_budget.py` from the testing folder of the shared tools, found below the module's
root, and the command runs it with the interpreter that runs the CLI. The JUnit file is
`junit.xml` in the tree's `Testing` folder. A repository without the reader, such as sushicore, prints no line;
a run that wrote no file prints a warning in its place. The shards of a build write `test_results/gtest/<shard>.xml`; the
command empties that folder before a run and hands it to the reader as `--cases`. `ModuleTests.run_program` runs a test
program by the name its CTest tests carry; without it a failed shard reruns whole. `ModuleTests.rebuilt` says whether the tree was current
when the run began, which a CLI answers with `CMakeDriver.tree_is_current`; when it is absent the line ends "(not rebuilt)" and never
gates, and a sanitizer run is always rebuilt.

The reader runs twice. The first call, with `--list-over`, writes the tests over a limit to
`over_limit.txt` in the tree's `Testing` folder; `SlowTestRerun` reruns them alone into `test_results/slow/<shard>.xml` or `slow_junit.xml`; the second
call, with `--gate`, judges each by its time alone and its exit code becomes the run's when CTest passed. A reader that
cannot judge the run, such as one older than this command, fails it. `programs.json` there maps each suite to its program
for `--programs`, and `resources.json` is the resource file CTest gets as `--resource-spec-file`.
