# Command line interface

**Describes:** `source/sushicore/command_surface/verbs.py`, `source/sushicore/command_surface/panels.py`, `source/sushicore/command_surface/options.py`, `source/sushicore/command_surface/sanitize_option.py`, `source/sushicore/command_surface/build_command.py`, `source/sushicore/command_surface/run_command.py`, `source/sushicore/command_surface/bench_command.py`, `source/sushicore/command_surface/check_command.py`

Every Sushi CLI (`se`, `sr`, `sa`, `sb`, `sd`, `sl`, `sp`, `st`) answers to the same verbs, lists
them under the same help panels and spells their flags alike, so a person who knows `se build`
knows `sd build`. This page is the canonical surface. Each CLI's own guide,
`docs/guides/COMMAND_LINE_INTERFACE.md` in its repository, follows it: the sections below in the
same order, a verb that does not apply named as absent, and the CLI's own commands and flags after
the canonical ones. How a CLI registers each verb is in [CLI integration](CLI_INTEGRATION.md).

## The verbs

A CLI registers every verb that applies to its repository. `K_CANONICAL_VERBS` in
`sushicore.command_surface` lists them, and `assert_registers_verbs(app, excluded=...)` fails a
CLI's test when one that applies is missing.

| Verb | Panel | Does | Declared by |
| --- | --- | --- | --- |
| `setup` | Environment | Provisions what the module needs to build, then runs `doctor` | `register_provision_commands` |
| `doctor` | Environment | Reports the checks of the module | `register_provision_commands` |
| `link`, `unlink` | Environment | Records the module in a workspace, or removes it | `register_provision_commands` |
| `build` | Build | Configures the tree of a build type when needed, then builds it | `register_build_command` |
| `test` | Build | Runs the tests of the tree by size label and prints the budget line | `register_test_command` |
| `run` | Run | Starts a built program, or offers the built examples to pick from | `register_run_command` |
| `bench` | Run | Runs the built benchmark programs; a benchmark measures and never fails | `register_bench_command` |
| `check` | Build | Runs the repository's checkers under `tools/` | `register_check_command` |
| `clean` | Build | Lists the build trees a filter selects and removes them only with `--yes` | `register_clean_command` |
| `package` | Build | Installs a built tree to a prefix and archives it | `register_package_command` |
| `docs` | Build | Builds the API reference and bundles the published pages | `register_docs_commands` |
| `config`, `env` | Environment | Prints every resolved setting, or the environment build processes run under | `register_diagnostic_commands` |
| `where` | Environment | Names where a file the CLI reads lives | the CLI |
| `status` | Environment | Prints the state of the checkout and its build trees | the CLI |
| `backlog`, `design` | Records | Read and change the backlog and the design topics | `register_backlog_commands`, `register_design_commands` |

## The panels

The help page groups commands by panel, in the order each panel's first command is registered. A
CLI registers in this order: Build, Run, its domain panel, Environment, Records. `CommandPanels`
holds the order and refuses a domain panel named like a canonical one; `panel_of(verb)` returns the
panel of a canonical verb.

| Panel | Holds |
| --- | --- |
| Build | `build`, `test`, `check`, `clean`, `package`, `docs` |
| Run | `run`, `bench` |
| The domain panel | The CLI's own commands, such as `sa train` or `sd host`; one panel at most |
| Environment | `setup`, `doctor`, `link`, `unlink`, `config`, `env`, `where`, `status` |
| Records | `backlog`, `design` |

## build

| Flag | Takes | Does |
| --- | --- | --- |
| `--type`, `-t` | One of the CLI's build types | Builds the tree of that type; each type has a tree of its own. The default is the CLI's, usually `debug` |
| `--sanitize` | `KINDS`, comma-separated: `address`, `undefined`, `thread` | Builds with the sanitizers `sushi_sanitizers` adds, in a tree of their own. The order does not matter, and `address` with `thread` is refused |
| `--define`, `-D` | `VAR=VALUE`, repeatable | Passes a CMake cache variable to configure. The tree keeps it; `VAR=` clears it |
| `--jobs`, `-j` | `N` of 1 or more | Compile jobs at once; when absent, the `build_jobs` key of `[tool]` in the config, else the hardware threads less four, at least one (`CMAKE_BUILD_PARALLEL_LEVEL` sets the threads counted) |
| `--no-test` | | Builds no test programs |
| `--report`, `-r` | | Prints the edges the build compiled by kind, with their time and memory; passed to the CLI's build service as `report` |

## run

| Flag | Takes | Does |
| --- | --- | --- |
| `TARGET` | A program name | Runs the program of that exact name, else the one whose name holds it |
| `--type`, `-t` | One of the CLI's build types | Runs the program from the tree of that type; the default is the CLI's, usually `debug` |
| `--pick` | | Offers the built examples to choose from |
| `--all` | | With `--pick`, lists the test and benchmark programs as well |
| `--no-build` | | Runs what is built, building nothing first |
| `-- ARGS` | Anything | Goes to the program unchanged |

`--sort`, or the old flag a CLI had, is a hidden spelling of `--pick` that names its replacement.

## bench

| Flag | Takes | Does |
| --- | --- | --- |
| `--type`, `-t` | One of the CLI's build types | Runs the benchmark programs of that tree; the default is the type a timing is taken on, usually `release` |

## check

| Flag | Takes | Does |
| --- | --- | --- |
| `--report`, `-r` | | Prints the finding count of each rule without failing |
| `--rule` | `NAME` | Runs that rule alone |

`test`, `clean`, `package`, `setup`, `doctor`, `link`, `unlink`, `config` and `env` take the flags
[Command surface](../reference/COMMAND_SURFACE.md) lists.

## Flags of a CLI's own

A CLI adds a flag to a canonical verb only for what its repository has and the others lack, such as
`sa build --distributed` or `se build --backend`. Its guide lists the flag in the verb's section,
after the canonical ones. A flag that two CLIs give the same meaning is spelled the same in both;
when a third needs it, it moves into SushiCore.
