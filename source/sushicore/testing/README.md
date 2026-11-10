# sushicore.testing

The `test` command every Sushi CLI with CTest tests registers, and the pieces it is built from. The
rules it carries out are the `testing` skill's: a default of `small` and `medium`, no `large` run
without a filter, and one budget line after every CTest run. Its options are in
[Command surface](../../docs/reference/COMMAND_SURFACE.md).

## What it owns

| Name | File | Does |
| --- | --- | --- |
| `TestLabel`, `LabelSelection`, `select_labels`, `large_needs_a_filter` | `labels.py` | Name the labels `--label` accepts, turn them into the `ctest -L` and `-LE` patterns, and say when a run would start the `large` tests unfiltered |
| `scope_of`, `reader_command`, `print_budget` | `budget.py` | Decide what a run is judged as, build the call of the budget reader and print its line |
| `ModuleTests`, `SanitizedTests`, `TestConsole` | `module_tests.py` | What one module CLI hands the command: its tree, its CTest call, its checkout and its console, and the sanitizer builds and the pytest suite it may add |
| `choose_jobs`, `JobChoice`, `share_of` | `job_count.py` | Pick the job count of a run given none: one per core, lowered so the jobs' memory shares fit the free memory, a `small` run at 256 MB per test and any other at 1024 MB, and the line that prints it |
| `registers_shards`, `program_of`, `program_executable`, `gtest_results_folder`, `rerun_results_folder` | `shards.py` | Tell whether a build registers its cases as shards, name the program of a shard, find the executable its shards run and name the folders a run leaves their results in |
| `ProgramRunner` | `program_runner.py` | Run a test program of a tree by the name its shards carry, under the module's environment; a CLI hands it to `ModuleTests` as `run_program` |
| `failed_tests`, `failing_cases`, `ResultFileError` | `result_files.py` | Read the failed CTest tests from the JUnit file and the failing `Suite.Case` names from a shard's GoogleTest XML |
| `FailedTestRerun`, `RerunOutcome` | `rerun.py` | Rerun the failed tests once, alone: a failed shard's failing cases by `--gtest_filter` on its program, any other test by `ctest -R`; tell flaky from failing |
| `run_tests` | `session.py` | Refuse a run that cannot start, build a sanitizer tree when asked, empty the shard results, run CTest with a JUnit file, rerun what failed and print the budget line, or hand the labels to the CLI's own pytest suite |
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
program by the name its CTest tests carry; without it a failed shard reruns whole. `ModuleTests.rebuilt` says whether the tree was rebuilt
just before the run; when it is absent the line ends "(not rebuilt)" and never gates, and a sanitizer run is
always rebuilt.
