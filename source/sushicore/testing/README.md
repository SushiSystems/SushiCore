# sushicore.testing

The `test` command every Sushi CLI with CTest tests registers, and the pieces it is built from. The
rules it carries out are the `testing` skill's: a default of `small` and `medium`, no `large` run
without a filter, and one budget line after every run. Its options are in
[Command surface](../../docs/reference/COMMAND_SURFACE.md).

## What it owns

| Name | File | Does |
| --- | --- | --- |
| `TestLabel`, `LabelSelection`, `select_labels`, `large_needs_a_filter` | `labels.py` | Name the labels `--label` accepts, turn them into the `ctest -L` and `-LE` patterns, and say when a run would start the `large` tests unfiltered |
| `scope_of`, `reader_command`, `print_budget` | `budget.py` | Decide what a run is judged as, build the call of the budget reader and print its line |
| `ModuleTests`, `SanitizedTests`, `TestConsole` | `module_tests.py` | What one module CLI hands the command: its tree, its CTest call, its checkout and its console, and the sanitizer builds and the pytest suite it may add |
| `run_tests` | `session.py` | Refuse a run that cannot start, run CTest with a JUnit file, print the budget line |
| `register_test_command` | `commands.py` | Add `test` to a Typer application |

The package re-exports `register_test_command`, `ModuleTests`, `TestLabel`, `LabelSelection` and
`select_labels` and `SanitizedTests`; the other names are the package's own and no CLI imports them.

## What it depends on

Inside sushicore, only `sushicore.profile`; Typer is imported when the command is registered. A module
supplies its CTest call, so the package imports no build driver.

The budget reader is `test_budget.py` from the testing folder of the shared tools, found below the module's
root, and the command runs it with the interpreter that runs the CLI. The JUnit file is
`junit.xml` in the tree's `Testing` folder. A repository without the reader, such as sushicore, prints no line;
a run that wrote no file prints a warning in its place.
