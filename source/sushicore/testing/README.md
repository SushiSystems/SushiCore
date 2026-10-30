# sushicore.testing

The `test` command every Sushi CLI with CTest tests registers, and the pieces it is built from. The
rules it carries out are the `testing` skill's: a default of `small` and `medium`, no `large` run
without a filter, and one budget line after every run. Its options are in
[Command surface](../../docs/reference/COMMAND_SURFACE.md).

## What it owns

| Name | File | Does |
| --- | --- | --- |
| `TestLabel`, `LabelSelection`, `select_labels` | `labels.py` | Name the labels `--label` accepts and turn them into the `ctest -L` and `-LE` patterns |
| `scope_of`, `large_needs_a_filter`, `reader_command` | `budget.py` | Decide what a run is judged as, refuse an unfiltered `large` run, and build the call of the budget reader |
| `ModuleTests` | `module_tests.py` | What one module CLI hands the command: its tree, its CTest call and its checkout |
| `run_tests` | `session.py` | Check the tree, run CTest with a JUnit file, print the budget line |
| `register_test_command` | `commands.py` | Add `test` to a Typer application |

The package re-exports `register_test_command`, `ModuleTests`, `TestLabel`, `LabelSelection` and
`select_labels`. Every other name is private to it.

## What it depends on

Nothing outside `sushicore.profile`. A module supplies its CTest call, so the package imports no
build driver. The budget reader is `test_budget.py` of the shared tools a repository carries, run through the
command the module supplies; a repository without it prints no budget line.
