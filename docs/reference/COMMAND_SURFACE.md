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
| `test` | `--label` or `-l` (repeatable), `--filter` or `-f`, `--repeat` or `-r`, `--jobs` or `-j`, `--all` | Runs the tests of the build tree, `small` and `medium` unless a label is named, writes a JUnit file, then prints the budget line when the repository carries the budget reader. The labels are `small`, `medium`, `large` and `quarantined` |

`--label large` without `--filter` exits `2` before anything runs; `--all` runs every size. The budget line
is a report and never changes the exit code, which is CTest's. A tree that is absent or stale also exits `2`.

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
