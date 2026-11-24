# Architecture overview

SushiCore is one Python package, `sushicore`, with ten sub-packages. Seven CLIs import it:
`hub`, `sr`, `se`, `sa`, `sb`, `sd` and `st`. It registers commands on their Typer applications
and has no application of its own.

## The modules

### Locating a project and loading its configuration

| Module | Owns |
| --- | --- |
| `layered_toml` | `read_toml`, `walk_up` and `has_marker`, `resolve_env_path`, and `load_layered`, which merges the `[tool]` table with its platform override and the environment variables |
| `workspace` | The workspace marker and data file, and its `[modules]` table; it re-exports the `layered_toml` readers the module CLIs import from it, and answers the deprecated `load_layered`, `merge_platform_table` and the link functions from the modules that hold them |
| `link_pointer` | A module's `[link]` pointer to its workspace: `read_link`, `write_link` and `clear_link` |
| `files`, `files_memory` | `Files`, the port the backlog and design stores read and write their text files through; `DiskFiles`, its default on the real file system; `MemoryFiles`, which holds each file by path |
| `environment`, `environment_memory` | `Environment`, the port a config loader reads variables through; `ProcessEnvironment`, its default over `os.environ`; `MemoryEnvironment`, which holds each variable by name |
| `config_base` | `ToolConfig`, the tool-path fields every CLI shares, and the layered load and `[tool]` write around them |
| `module_config` | `ModuleConfig`: a module's project root and its layered config, the linked workspace's `[tool]` table included; `load` takes `root=`, `environment=` and `files=`, so a CLI test runs it with no disk and no process environment |
| `stack_config` | `StackConfig`: the compiler and vcpkg of a module that consumes a dependency root, and `locate_sibling` |
| `profile` | `ModuleProfile`: what one CLI says about itself, such as its name, command, environment prefix and root marker |
| `deps_fragment` | The one reader of a `sushistack.deps.toml` fragment |
| `errors` | `SushiCoreError`, the one base every exception class the package defines derives from, so a caller catches one type; `ConfigError`, `DigestMismatchError`, `ProjectRootNotFoundError`, `CommitMismatchError` and `KeyFingerprintMismatchError`, the failures an entry point prints as one line. Where a class also derived from a built-in, it keeps that built-in as a second base |
| `deprecated_name`, `moved_name` | `warn_deprecated`, the `DeprecationWarning` every restored name raises, naming its replacement and pointing at the caller; `moved_attribute`, what a module's `__getattr__` calls to answer a name that moved to another module |

### Printing

| Module | Owns |
| --- | --- |
| `config` | `load_appearance`: the `[cli]` table and the `SUSHI_CLI_*` variables resolved into one `AppearanceSpec`, read through the `environment=` and `files=` it is given |
| `theme` | `Theme`, the style tokens, and the presets `default`, `mono` and `muted` |
| `icons` | `IconSet`, the prefix printed before a line, and the presets `text`, `emoji`, `minimal` and `none` |
| `theme_registry` | `ThemeRegistry`, the named themes a console builder chooses from; `build_console` takes one as `theme_registry=` |
| `icon_registry` | `IconRegistry`, the named icon sets a console builder chooses from; `build_console` takes one as `icon_registry=` |
| `renderer` | The `Renderer` protocol and its three backends: `RichRenderer`, `PlainRenderer`, `JsonRenderer`; `TerminalMemoryRenderer` is the in-memory terminal tests use |
| `events` | The event kinds `JsonRenderer` writes and `event_line`, their one serialisation |
| `console`, `console_memory` | `Console`, the facade a CLI calls: `info`, `success`, `warn`, `error`, `command`, `header`, `fail_panel`, `table`, `progress`, `result`, `prompt`; `RecordingConsole`, which records every call in order |
| `cli_console` | `LazyConsole`, which builds the console on first use so `--help` runs outside a checkout |
| `markup` | `escape_unknown_tags`, which keeps a bracket as text unless it names a style |
| `terminal_background` | `is_dark_background`, decided from the `background` setting and `COLORFGBG` |
| `windows_console`, `console_api` | `enable_virtual_terminal` for a classic Windows console; `ConsoleApi`, the three kernel32 calls it makes |
| `brand` | The Sushi Systems mark and wordmark as palettes and pixel grids |
| [`ui`](../../source/sushicore/ui/README.md) | One file per terminal element, each drawn from a `Theme` |
| [`help`](../../source/sushicore/help/README.md) | A help screen as data and the page that lays it out |
| `typer_help` | `help_group`, which wires the help page into a Typer application |
| `typer_theme` | `apply_typer_theme`, which recolours Typer's own help screen |

`build_console` in `sushicore/console_builder.py` wires the printing modules together from the config
files a CLI hands it; the package re-exports it.

### Building

| Module | Owns |
| --- | --- |
| `proc`, `proc_memory`, `quiet_console`, `quiet_runner` | `CommandRunner`, the surface callers run commands through: `run` (with an optional `timeout` and `stdin`), `run_drained`, `run_quiet` (shows only the tail of a failure), `capture` (takes a list or a string command, an optional `timeout`, `input_text` for stdin and an `encoding`) and `capture_bytes` (undecoded output); in machine mode a child's output reaches the console as `line` events, never stdout. `Runner` spawns a child process for a CLI; `RecordingRunner` records the commands and answers scripted results. `QuietConsole` (`quiet_console`) is the console that drops all output but errors, and `quiet_runner` (`quiet_runner`) returns a `Runner` over it, for a caller that reads results and shows nothing; `build_gate` loads `quiet_console`, `proc`, `memory_reading` and `unit_peaks` by path, so none of them imports the package |
| `build_env`, `stack_build_config` | The environment a build runs under, with the vcvars snapshot on Windows; `StackBuildConfig`, the config fields it reads |
| `message_console`, `report_console` | `MessageConsole`, the four message calls a unit that only reports needs; `ReportConsole`, the header, info, error and table calls of a diagnostic report |
| `cmake_cache` | What a `CMakeCache.txt` says about how its tree was configured |
| `cmake_modules` | `K_CMAKE_MODULES`, the folder of the [CMake modules](../../source/sushicore/cmake/README.md) the package ships, and `with_cmake_modules`, which puts it on a configure's `CMAKE_MODULE_PATH` |
| `cmake_driver`, `cmake_driver_port`, `cmake_driver_memory`, `cmake_tool_config` | `CMakeToolConfig`, the tool paths and path expansion the driver reads from a config; `CMakeDriverPort`, what a CLI asks of a CMake driver: the cmake and ctest commands and what a build tree holds (`tree_exists`, `cached_value`, `configured_generator`); `CMakeDriver`, which runs them over real trees; `MemoryCMakeDriver`, which holds its trees in memory and records each call |
| `toolchain_args` | The compiler and vcpkg prefix arguments of a configure |
| [`docker`](../../source/sushicore/docker/README.md) | `DockerEnvironment`, the `docker build` and `docker run` of a module's developer image, named by a `DockerImage` |
| `discovery` | `ExecutableIndex`, the built executables under a build tree, and the choice `run --pick` offers; `select_interactive` asks through the console the index was made with |
| `example_catalog` | `ExampleCatalog`, the examples a repository registers under `applications/examples/`, each with the `@brief` of its source |
| `run_options` | `pick_option`, `list_all_option` and `old_pick_option`: the `--pick`, `--all` and old `--sort` options of a `run` command, declared once |
| `run_program` | `run_program`: resolves a program under a build tree through an `ExecutableIndex` and runs it from the project root |
| `clean_command` | `register_clean_command`, `select_trees` and `clean_trees`: the `clean` command, which lists the build trees a `--type` or `--sanitize` filter selects and removes them only with `--yes` |
| `build_tree` | The tree a build type builds in, `build/<name>-<type>`, and the refusal of any other type in it |
| `build_admission` | The launcher entries that put a tree's compiles and links behind the gate, and the job count |
| `build_gate` | The memory gate itself, the script every compile and link of a tree runs through |
| `memory_reading` | The physical memory free now, and the share kept back from every user of it; read by `build_gate` and by the test job count |
| `unit_peaks` | `UnitPeaks`, the peak each build unit was last measured at and its kind, from which a kind's largest peak and unit count are read; written by `build_gate` and read by `build_report`, and it imports nothing from the package so `build_gate` loads it by path |
| `build_report` | What each kind of edge of one build cost in time and peak memory |
| `build_trace` | What the clang time traces of a build say: the costliest headers and templates, and each unit's frontend and backend time |

### The surfaces every CLI registers

| Module | Owns |
| --- | --- |
| `root_options` | `--version` and `--describe` |
| `describe` | The command catalogue `--describe` prints as JSON |
| `diag`, `diag_memory`, `diag_commands` | `Diagnostics` and the `config` and `env` commands registered from it; `InMemoryConfigModule`, the config module it reads in a test |
| `aliases` | `AliasTable`: old spellings that still run, hidden, and name their replacement |
| `entry` | `run`, the entry point that turns a `SushiCoreError` into one line and exit code 1 |
| [`provision`](../../source/sushicore/provision/README.md) | The dependency root, the registry, the doctor and the commands `setup`, `doctor`, `link`, `unlink` |
| [`docs_bundle`](../../source/sushicore/docs_bundle/README.md) | The `docs` command group and the documentation bundle `docs bundle` writes |
| [`testing`](../../source/sushicore/testing/README.md) | `register_test_command`, the `test` command of every CLI with CTest tests, and the pieces it is built from |
| `command_surface` | The canonical verbs and panels, `register_build_command`, `register_run_command`, `register_bench_command` and `register_check_command`, the service each calls, the shared `--sanitize` option and `assert_registers_verbs` |
| [`backlog`](../../source/sushicore/backlog/README.md), [`design`](../../source/sushicore/design/README.md) | The `backlog` and `design` command groups, and the stores of `docs/backlog/` and `docs/design/` they read and write |
| `command_groups` | The names of the groups a CLI adds beside its own commands, and the check that it exposes them |
| [`tools`](../../source/sushicore/tools/README.md) | The checkers every repository runs with `python -m sushicore.tools check .`, and its git hooks |
| [`release_train`](../../source/sushicore/release_train/README.md) | Releases a library and every library that pins it, in dependency order |

## Rules the code keeps

- `Console` talks to the `Renderer` protocol. A renderer is any object with the protocol's eight
  methods (`line`, `command`, `header`, `panel`, `table`, `progress`, `result`, `prompt`) and its
  `raw` property, which `Console.console` hands out as the Rich console. `Console.is_machine` asks
  whether the renderer is a `JsonRenderer`.
- `Theme` and `IconSet` are data. A new preset is registered on a `ThemeRegistry` or
  `IconRegistry` the caller passes to `build_console`; no other module changes. `register_theme` and
  `register_icon_set` stay one release as deprecated shims over the default registries.
- A component in `ui` imports `Theme`, `brand`, `markup`, the component base and Rich, and nothing
  else. `tools/layering/check_package_layers.py` reports one that imports more.
- `typer_help` is the only module that imports Typer when it is loaded. `typer_theme`,
  `root_options`, `diag_commands`, `provision/commands.py`, `docs_bundle/commands.py` and the
  modules of `command_surface` import it inside the function that needs it, and `aliases`, `describe` and `entry` only for type checking, so `import sushicore`
  works without the `typer` extra.
- Inside `provision`, lower layers do not import higher ones; the layer table is `K_LAYERED` in
  `tools/layering/check_package_layers.py`, which fails an import that breaks it.

## Why each module is shaped as it is

### The package

`sushicore` holds two things. The first is a config-driven presentation layer: `build_console`
assembles a `Console` from layered TOML config and the environment, using the `theme` and
`icons` presets and one `renderer` backend. The second is the build machinery that decides what
reaches a compiler in five of the consuming repositories: `proc.Runner` spawns, `cmake_cache`
reads `CMakeCache.txt`, `cmake_driver.CMakeDriver` writes the cmake and ctest invocations, and
`toolchain_args` derives the compiler and the vcpkg prefix. Each consumer's own
`services/project.py` keeps its build policy and calls into these.

### `build_tree`

Every build type has a tree of its own, `build/<name>-<type>`, and Debug is the type a CLI builds
unless told otherwise. Switching between Debug and Release then recompiles nothing: each tree
keeps its objects. `refuse_another_build_type` stops a configure that would give a tree a type
other than the one its cache holds, and any `-D CMAKE_BUILD_TYPE` passed beside `--type`, since
either would recompile the whole tree under the other type's flags while its name says otherwise.

`package_build_type` gives the type of the library packages a consumer links: Release for a
Debug, MinSizeRel or sanitized consumer, which runs against the release runtime and the Release
packages beneath it, and RelWithDebInfo for its own kind.

### `tree_reuse`

A build never removes a tree. `refuse_unreusable_tree` stops one whose generator is not the one the
build uses, or that was configured for another source folder, because CMake cannot change either in
place; the message names `<program> clean`. Every other difference, such as an option or a define,
is configured in place. The tree is read through the driver, so an in-memory tree is judged the way
a real one is.

### `build_admission`

A CLI passes `launcher_defines` to its configure and compiles at the count `resolve_jobs` gives; the test command hands that count over exactly only for an explicit `-j`, and otherwise as a ceiling that `choose_jobs` lowers to fit free memory. `default_jobs`
is `hardware_threads` less four, at least one; `hardware_threads` is the raw count, or
`CMAKE_BUILD_PARALLEL_LEVEL` when it is set. `resolve_jobs` takes `-j`, else the `build_jobs` key, else `default_jobs`. Every compile
and link of the tree then runs as `python -I build_gate.py <state> [--cache <ccache>] -- <command>`.
The state folder, `build/build_gate`, sits beside the trees and every tree of a checkout shares
it, so two builds at once share one memory budget and a unit measured in one build type is known
to the others. `refuse_a_stopped_gate` refuses a build while the folder holds a file named `stop`.

`compiler_cache` gives the ccache executable from the CLI's `ccache_exe` setting, or from `PATH`
when the setting is empty; a configured path that does not exist gives none.

### `build_gate`

The gate runs on its own, with the standard library only, and loads its siblings by path: it starts once per edge, and importing
the package would cost more than most host compiles. It admits an edge when the edge's measured
peak, added to the peaks reserved by the edges already running, fits in the larger of the memory
free when the gate was last idle and the memory free now, each less 1.5 GB, and at least 1.5 GB is
free. An edge that finds nothing running is always admitted. Edges are admitted in
arrival order. A lighter edge may pass a waiting one for up to 10 s, then the queue drains, so a
heavy unit is never starved and Ninja can run at the hardware thread count without a pool sized
for the worst unit.

Each edge's peak is measured as it runs, through a job object on Windows and the children's peak
resident set on Linux, and kept per unit and optimisation level, with the unit's kind, in
`unit_peaks.json`. A measurement the compiler ran for in full replaces the unit's peak, so a unit
that grew lighter is reserved at what it needs now. A host compile may be answered by ccache, which
costs almost nothing, so its measurement only raises the peak. A kind's largest peak and its unit
count are read from the units held now, never stored apart, so a heavy unit that grew lighter or left
the kind stops weighing on it. A unit not seen before is reserved at the larger of its kind's default
and the largest peak of its kind, so light units measured first never let two unmeasured heavy ones
in together. Once ten units of a kind are measured, it is reserved at twice the largest peak instead,
no lower than a quarter of the default, no higher than the default and no lower than the largest peak seen. A file of another form holds
no unit, and the next build measures them again. While `stop` exists, each waiting or new edge fails and the running ones finish, which
stops a build without killing a process.

With `--cache`, a host compile runs through ccache, capped at 5 GB in `build/ccache` and checking
the compiler by its content, unless the environment already sets those, as a CI job does. A compile
with `-fsycl` never does: its object carries device images, and a stale one is a kernel missing at
run time that no build step would report. The gate writes to standard error, which Ninja shows as
the edge's output, so it has no logger.

When the state folder holds `time_trace.txt`, one unit key per line (`request_time_traces` in
`build_admission` writes it, `clear_time_traces` removes it), the gate adds `-ftime-trace` to the
compile of each listed unit, host or device, and runs it without the cache, which would answer
with no trace.

A host compile that succeeds has its object read for a SYCL kernel submission it instantiates,
`handler::parallel_for` or `single_task` as MSVC or Itanium mangle them. A unit compiled without a
device pass that instantiates one defines a copy with no device image behind it; the linker may keep
that copy over a device unit's, and the kernel is then missing at run time with nothing in the build
to say so. Only the symbols the object defines count, read from an ELF64 or COFF symbol table:
the debug information of a `-g` build names submissions the unit only references. An object in
another format is searched whole. The gate deletes such an object and fails the edge, naming the
symbol.

### `build_report`

`of_build` reads the edges one build ran from the records `.ninja_log` gained during it, tells
host and device compiles and links apart from `compile_commands.json` and `build.ninja`, and joins
the gate's peaks. The report gives, per kind of edge, the count, the total and longest time and
the peak memory, with the lowest free memory, the slowest edges and the heaviest units.

### `build_trace`

`summarise_time_traces` reads every clang `<object stem>.json` that sits beside an object under a
tree and sums, over all units, the `Source` events (a header, by path), the `InstantiateClass`
and `InstantiateFunction` events (a template, by name) and each unit's `Total Frontend` and
`Total Backend`. `TraceSummary.lines()` prints the top headers and templates with the number of
units that paid for each, then the units slowest first. A header's time includes the headers it
includes, so the totals overlap by design; the ranking tells which header to trim, not what a
build would save. Traces come from `build_gate` on the units `build_admission` requests.

### `build_env`

A parent process cannot `call vcvars64.bat` and inherit the result: the batch file sets its
variables in its own shell, which then exits. So the shell runs as a child, its environment is
dumped and parsed, and that dictionary is handed to every cmake and ctest subprocess. The
snapshot is cached on disk, keyed by the configuration that produced it, so an unchanged config
skips the shell.

`StackBuildEnv` composes them the way a module that consumes the shared toolchain needs.
SushiRuntime selects a toolchain instead of consuming one, and composes the primitives itself.

`RUNTIME_DEVICE_VARS` names the variables that pick which accelerator a program runs on. The
snapshot dumps the whole environment of the shell that produced it, so a variable exported for
one debugging session would be frozen into the cache and replayed into every later build and
run. A fresh terminal would not escape it, because the snapshot is merged over the current
environment. These variables name a run-time choice and never a toolchain fact, so they are
dropped when the cache is written and again when it is read. `CALLER_TEMP_VARS`, `TMP` and `TEMP`,
are dropped the same way: they name the folder a compiler writes its temporaries to, so a caller
that points them at another drive is obeyed and the snapshot does not pin them to the drive it
was taken on.

`tests/test_build_env.py` guards both sides. The defect behind
`test_a_cache_written_before_this_existed_heals_on_read` was a snapshot taken while a session
had pinned SYCL to the CPU: it kept pinning every later build and run, from any terminal,
because the cache is merged over the current environment.
`test_a_callers_device_choice_survives_the_merge_with_a_cached_snapshot` checks the other side. Dropping the
variable from the snapshot must not stop a caller setting it for one run; `merge_env` starts
from the live environment, so a deliberate export still arrives.

On Windows the runtime DLL pulls in dependencies that vcpkg installed, hwloc among them, so
`StackBuildEnv` puts the vcpkg installed `bin` folder on `PATH` for that DLL to load.

### `cli_console`

Constructing a console needs the repository's `cli/` config directory, and locating that walks
up for a root marker, which fails outside a checkout. Doing it at import time makes every
invocation of a CLI abort with "Not inside a … project", including the ones Typer can answer
with no project at all: `--help`, and `sr toolchain`.

Four of the five CLIs had found that out, and each fixed it with its own copy of the same
PEP 562 module-level `__getattr__`. sushiengine's copy never received the fix, so `se --help`
outside a checkout still failed while the other four worked.

### `cmake_driver`

`CMakeDriver` knows the shape of a cmake command line. It does not know the name of a single
cache variable: which `-D` flags a module passes, which targets it has and which suites it runs
are policy, and policy stays in the module. Everything specific to a module arrives as a
parameter: `expect` for the cache entries a tree must already agree with, `targets` for what to
build, `label_regex` for which tests to select.

`configure` adds the folder of SushiCore's CMake modules to `CMAKE_MODULE_PATH`, after any
folders the argv names, so a project writes `include(SushiBuild)` and finds the build policy and
the helpers every Sushi C++ repository shares. The modules choose the linker themselves, lld
through `CMAKE_LINKER_TYPE`, so the driver asks the compiler nothing.

`configure` deletes `CMakeCache.txt` first when the tree was configured with a C++ compiler at
another path than the one the argv names. CMake would otherwise delete the cache itself and
run the configure a second time without the `-D` values of the command line, which leaves a
tree with default options: targets go missing and the build type is lost. This happens to
every build tree after the dependency root moves. The comparison ignores case and separators
as the platform does, and an argv that names no compiler leaves the cache alone.

`compile` points `TMP` and `TEMP` at `compiler_tmp` inside the build tree and deletes that
folder when the build ends, whether it passed, failed or raised. A SYCL link that targets CUDA
leaves its device-split files, about 150 MB per executable, in the temp folder and never removes
them; in the shared `%TEMP%` they reached half a million files. The scratch folder belongs to one
tree, so two trees building at once never empty each other's.

In `doxygen`, the child resolves its argument against `cwd`, and every module passes a path
relative to the project root, not an absolute one. The method derives that path from the
Doxyfile so a caller does not give it twice. It needs `as_posix()` on Windows, where
`relative_to` yields backslashes and `str()` would change the command line.

`tests/test_cmake_cache.py` already pins the comparison inside `is_stale`: case and separator
handling, an unconfigured tree and the rest. The `root` tests in `tests/test_cmake_driver.py`
are about how `needs_configure` wires that check in. Passing `root` turns the check on, it
warns when it fires, and omitting `root`, which is what every call site did before the
parameter existed, leaves an otherwise fresh tree alone.

### `config`

`config` resolves which theme, icon set and colour mode to use. It knows nothing about how a
repository finds its own config directory. That discovery, such as the walk up for a marker
file, is specific to a repository and stays in each CLI. The module only merges the list of
TOML files the caller hands it, highest precedence last, with the environment variables on top.
That keeps one seam: every Sushi CLI points this loader at its own `config.toml` and
`config.local.toml` and gets the same merge behaviour. The schema of the `[cli]` table is in
[Configuration](../reference/CONFIGURATION.md).

### `config_base`

Every module CLI (`sr`, `se`, `hub`) shells out to the same host build tools: cmake, ninja,
vcpkg, and a vcvars batch file on Windows. So each carries the same tool-path fields and the
same layered load and `[tool]` write around them. That generic part is `ToolConfig` and its two
helpers.

The module knows nothing about SYCL, toolchains or any module's compute schema. A CLI that
provisions a SYCL toolchain subclasses `ToolConfig` and adds those fields in its own
repository.

`build_jobs`, a whole number, is the job count of a build and a test run; 0 or absent means `default_jobs`.

Three of the fields exist because of where Windows installs the tools:

- `cmake_exe` and `ctest_exe` are resolved from `PATH` when empty. They are configurable
  because VS BuildTools does not ship the CMake component, so on Windows cmake commonly lives in
  a scoop or standalone install that is not on `PATH`.
- `rc_exe`, the resource compiler, is resolved from the default of `CMAKE_RC_COMPILER` when
  empty. It is configurable because clang-cl and intel-llvm toolchains often fail to probe for
  `rc.exe` on Windows.
- `doxygen_exe` is resolved from `PATH` when empty. It is configurable because on Windows
  doxygen commonly installs outside `PATH`, behind winget or choco shims or under Program Files.

### `deps_fragment`

A fragment is one table per dependency, keyed by its name, and two reserved tables that carry
metadata instead of a dependency: `[module]`, and `[sushisystems]` with the pins of the Sushi libraries
the module links. No dependency can be named `module` or `sushisystems`. Several CLIs read the format, so it is read here
once. Two readers of one file is how a required dependency goes missing without a word, which
is what happened to sushidsp's fragment until 2026-09-22.

The module reads and reports. It runs no package manager: whether a package is installed is a
question only a package manager answers, and which one to ask is the caller's concern. The
module answers what the file says, which command would satisfy an entry on a given platform
and, when an entry declares a `check_cmd`, whether that check passes.

### `diag`

`config` and `env` are read-only troubleshooting. When a build picks the wrong compiler or a
path looks off, `config` answers what was resolved and where each value came from: the default,
`config.toml` or an environment override. `env` answers which environment cmake and ctest run
under.

Four CLIs carried a copy of this and drifted in four ways: the program named in the prose, the
environment tokens counted as relevant to a build, which resolved directories were printed, and
how the build directory was found. A `ModuleProfile` and the config already know the first
three. The fourth is the caller's, so it is passed in.

`config_show` marks a config file as `(found)` or `(absent)` in parentheses, because Rich
parses `[found]` as a style tag and drops it.

### `discovery`

Every Sushi CLI has to answer the same question, "which of the files under `build/` is a
program I can run?", and every one of them answered it with its own copy of this walk. The
copies drifted in one place: which sibling directories to skip, because a module that builds a
dependency in-tree must not offer that dependency's executables as its own.

So the walk lives in `discovery` and the skip list is the caller's, supplied once when it
builds an `ExecutableIndex`, beside the search depth. Nothing else about the search is
configurable, on purpose:
`sr run`, `se run`, `sa run` and `sb run` should not be able to disagree about what counts as
an executable.

A prompt whose input has ended, or that Ctrl+C stops, picks nothing and says so, so a script
that runs a CLI with no terminal fails at once and does not wait.

`run --pick` offers the built examples, not every program: a build holds the tests and the
benchmarks beside them, and `sr test` and `sr bench` run those. `run_program` passes
`ExampleCatalog.in_project(root)` to `resolve`, and `list_all` brings back the whole list.
A build with no registered example lists every program, so a repository without examples
changes nothing.

Shared objects on Linux come as `*.so` and as versioned names such as `*.so.1`. The suffix
check misses the versioned ones, so the walk matches the substring `.so`.

`ExecutableIndex` imports nothing from Rich: `select` prints through the `table` and `prompt` of
the console it is given, and `find` and `match` run on every `run`. An index made with
`console=` answers `select_interactive(build_root)` through that console, so a CLI binds its
console once instead of wrapping `select`.

### `example_catalog`

The repositories register their examples in different ways: a wrapper function named after the
repository, a bare `add_executable`, a `CMakeLists.txt` in a folder of its own.
The catalog reads all of them, so the list of examples is the repository's own registration and
no second list exists to drift from it. It reads every `CMakeLists.txt` under the folder,
the folder's own first, and takes each call to `add_executable` or to a function ending in
`add_example` whose first argument is a literal name. A name built from a variable is the
wrapper's own body and is skipped, and so is a call in a comment.

The description is the `@brief` of the source the target is named after, or of its first
source. A target with no readable source has an empty description.

### `run_options`

Every `run` command that picks a program declared the same three options, `--pick`, `--all`
and the hidden old `--sort`, and each CLI spelled them out again. They are declared once, as
`testing.options` declares `--label` and `--filter`: `pick_option()`, `list_all_option()` and
`old_pick_option(table, old, *names)`. A CLI that never had `--sort` passes no old option; one
whose old flag had another name, such as `--select`, gives its names.

### `run_program`

Resolving a program and starting it is the same few lines in every CLI: resolve the target, the
pick or the default through `ExecutableIndex`, name the program, then run it from the project
root under the tree's environment. `run_program` is those lines. A CLI keeps what is its own
around the call, such as a build before the run or a memory limit, and hands over the tree, the
environment and the runner it already has.

### `clean_command`

Six CLIs declared their own `clean`, and each removed every build tree the moment it was typed.
A build tree of a large project costs hours, so the shared command removes nothing without
`--yes`: it says which trees the filter selects would be removed, with their sizes, and exits with code 2, which a script that
expected them gone cannot mistake for success.

The command knows the trees of the CLI, because the CLI hands it the tree name of each sanitizer
and the build types it builds. `--type debug` selects the plain `default-debug` tree and no other,
`--sanitize address` selects the trees of that sanitizer, and with neither every tree is
selected. A CLI whose `--type` also picks a sanitizer, as `sr build --type asan` does, names
those types in `type_trees`, so `sr clean --type asan` removes `asan-release`. A CLI that keeps more than trees under `build/`
may offer `--all` with `whole_build`, which selects the whole folder and takes no `--type`.
`with_all` names the folders a clean that no filter narrows removes beside the trees, such as an
assembled package folder, and `extra` offers one more flag that selects its own folders instead
of the trees, such as evaluation output that a clean of the build must never take. A CLI whose
`--type` names a tree and not a build type, as `se clean --type editor` does, hands `named` the
folders each name selects. A tree exists when the driver says so through `tree_exists`, which the
in-memory driver answers from memory, and otherwise when the disk holds it.
`build` does not delete a tree: removing one is `clean` and nothing else.

### `command_surface`

Eight CLIs declared `build`, `run`, `bench` and `check` each in its own words: `se`, `sr` and `st`
took `--no-test` and the others did not, `--sanitize address-undefined` in `sa`, `sb` and `se` was
`--sanitize address` in `sd`, `sl`, `sp` and `st`, and `run` sat under Project in four CLIs and
Build in the other four. The verbs, their panels and their flags
are declared once, and the CLI supplies only what differs: a service with one method that takes a
frozen request and returns the exit code. A command builds its Typer function from a list of
`CommandParameter`s, so a CLI adds its own options to a shared command without declaring the
command again, and its service reads them from `extra`. `--sanitize` takes the kinds
`sushi_sanitizers` builds and returns them in one order, so one set names one tree whatever order
it was typed in. The canonical page is [Command line interface](../guides/COMMAND_LINE_INTERFACE.md).

### `module_config`

Every Sushi CLI is installed outside the repository it builds, because pip or pipx puts it in a
venv, so the package's own location says nothing about where the project lives. The invocation
directory does. Each CLI therefore walks up from the working directory looking for one of its
markers: the checkout's marker file, or the release manifest an unpacked binary install
carries. It then layers `config.toml`, the workspace-shared `.sushistack/workspace.toml` in the workspace home
that `hub install` writes (the older `config.local.toml` in the hub checkout is read when it is absent), and the repository's own `config.local.toml`, in that order.

That is the same procedure five times over. It differs only in the marker, the project's name
in the error message and the prefix on the environment overrides, and a `ModuleProfile` already
states all three.

Outside a checkout the walk raises `ProjectRootNotFoundError`, a `SushiCoreError`. `entry.run` prints it as
one line and exits 1; a caller that can work without a project,
such as the console or `--help`, catches it.

### `profile`

The CLIs (hub, sr, se, sa, sb, sd and st) differ from each other in a handful of facts: a display
name, the command a user types, the prefix on their environment overrides, the file that marks
a project root, and which sibling checkouts they build in-tree. Everything else about locating
a project, layering config, listing executables and reporting diagnostics is the same work.

A `ModuleProfile` is the one place a module describes itself, and the shared machinery reads
it, so no CLI restates these facts in its own files.

It holds no behaviour beyond deriving names. A profile is data about a module, not a place to
hang a module's logic: anything specific to one CLI belongs in that CLI.

`RELEASE_MANIFEST` is the file the release build writes at the root of an unpacked binary
install. A module CLI reads nothing but its presence; `hub` reads the product, version and
platform inside it. The file is specified in section 5 of SushiStack's
`docs/design/HUB.md`.

`_TOOL_ENV_SUFFIXES` maps a config field to the suffix its environment override carries after
the module's own prefix. The table is shared because `ToolConfig`, whose fields it names, is
shared: it is the same knob on every CLI, so `SR_CMAKE` and `SE_CMAKE` must not be allowed to
mean different things.

### `proc`

`tests/test_proc.py` compares the resolved executable path without regard to case, and the
`Path` and `PATH` key the test is named for is only one reason. `shutil.which` on Windows
appends the extension exactly as `PATHEXT` spells it, `.EXE` by default, whatever the casing of
the file on disk (`tool.exe`). An exact string comparison fails there even though resolution
found the right file.

### `renderer`

`Renderer` is the seam the rest of the package depends on: the `Console` facade talks to this
protocol and never to Rich. Any object that implements its eight methods is a drop-in renderer.
Three ship in the file: `RichRenderer` for a terminal, `PlainRenderer` for text without markup,
and `JsonRenderer` for one event per line on stdout, the shape that section 7 of SushiStack's
`docs/design/HUB.md` fixes. `RichRenderer` takes the stream it writes to and the call that
switches on virtual terminal processing, and `force_utf8` switches given streams to UTF-8 and
records a stream that refuses; their defaults keep stdout and the Windows console switch.

### `stack_config`

SushiEngine, SushiAI and SushiBLAS are heads of the stack: they select no SYCL toolchain of
their own and consume the one `setup` or `hub install` provisions into a dependency root.
Resolving the compiler and vcpkg from those roots is identical work in all three, and each
carried its own copy of it.

SushiRuntime is not a subclass, by decision. It owns the bundle instead of consuming it,
selects between toolchains (acpp, clang++, icpx) and resolves dependencies with a different
signature. Forcing it into this shape would bend the base class around a case it does not
describe.

### `provision/sushi_packages`

A Sushi library compiled inside every consumer's build tree costs each consumer the SYCL
runtime. The sub-package gives every consumer a built package. One
file holds one job, so a rule changes in one place: the key (`package_key`), the source hash
(`source_state`), the configure inputs, the toolchain identity, the store with its locks and
its pruning, the per-consumer link, the builder that drives the library's own CLI, and the
resolver that composes them bottom-up. The resolver takes every collaborator through its
constructor, so each is replaced in a test and none starts a process there. The source hash is
of content and not of a commit, so a commit that touches only documentation changes no key.
The key lists the packages below it, so a library never links a dependency built against
another one than the closure's.

`RunDirs` keeps the run-time folders of the packages a tree linked in a file of that tree, so the
commands that run the tree resolve nothing again. `RunDirs.for_module(<module>)` names the file
`.<module>_package_dirs.json`, the name every module CLI uses.

### `theme`

`rule_line` styles the dashes either side of a `console.rule()` title and, through Rich's
theme-wide `rule.line` key, anything else that asks for that style. Its value `default` means
the terminal's own foreground colour: white on a dark terminal, black on a light one. A fixed
colour would be chosen without knowing the user's background.

`as_rich_styles` also sets the `bar.*` and `progress.*` keys. The built-in columns of
`rich.progress.Progress` read those theme keys directly. Overriding them themes `rich.progress`'s
`track` function and any bare `Progress(...)` in a downstream CLI with no change at the call site.

The preset registered as `default` and `sushiweb` is lifted from the palette in sushiweb's
`src/styles/global.css`. It is
near-monochrome, grey text on near-black or near-white, with a single amber accent (`#f0a500`)
in place of the many hues of a terminal default. The semantic colours are desaturated to sit
beside that accent instead of competing with it. The accent is reused for header rules and for
inline commands.

### `toolchain_args`

The file holds two derivations every cmake configure in the stack needs, and only two.
Assembling the full `-D` list is left out on purpose. SushiRuntime splits its assembly across
Windows and Linux, and SushiEngine omits `CMAKE_C_COMPILER` because its runtime lane has no C
sources. Both divergences are real and documented where they live. Forcing them into one
function would hide a real difference behind a flag.

### `typer_theme`

Typer with `rich_markup_mode="rich"` renders `--help` through Rich, but not through a `Theme`
object: it reads a set of module-level style constants in `typer.rich_utils` at render time.
There is no config seam to plug into, so patching those constants at startup is the only way to
make `--help` match everything else the package themes. That is why the colouring has its own
module. It is the one part of sushicore that reaches into another package's internals instead
of composing an abstraction.

### `workspace`

Every module CLI (`sr`, `se`, `hub`) resolves its config the same way: walk up for a marker
file, merge a `[tool]` table with its `[tool.<platform>]` override, then let `PREFIX_*`
environment variables win. That plumbing lives in `layered_toml`, so there is one seam; `workspace` names the marker and
keeps the `[modules]` table, and `link_pointer` edits a module's `[link]` table.

The module knows nothing about SYCL, toolchains or any module's schema. It only locates
directories and merges the TOML the caller hands it. Each CLI keeps its own `Config` dataclass
and passes in its markers, section name and environment-variable map.

`LEGACY_SHARED_CONFIG` is where `hub install` wrote the shared tool paths before 2026-09-22,
relative to the workspace root. It is read as a fallback so a workspace that no `hub` command
has upgraded yet still resolves.
