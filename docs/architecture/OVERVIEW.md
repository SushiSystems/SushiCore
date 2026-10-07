# Architecture overview

SushiCore is one Python package, `sushicore`, with three sub-packages. Seven CLIs import it:
`hub`, `sr`, `se`, `sa`, `sb`, `sd` and `st`. It registers commands on their Typer applications
and has no application of its own.

## The modules

### Locating a project and loading its configuration

| Module | Owns |
| --- | --- |
| `workspace` | The walk up to a marker file, the `[tool]` table merged with its platform override, the workspace's `[modules]` table and a module's `[link]` pointer |
| `config_base` | `ToolConfig`, the tool-path fields every CLI shares, and the layered load and `[tool]` write around them |
| `module_config` | `ModuleConfig`: a module's project root and its layered config, the linked workspace's `[tool]` table included |
| `stack_config` | `StackConfig`: the compiler and vcpkg of a module that consumes a dependency root, and `locate_sibling` |
| `profile` | `ModuleProfile`: what one CLI says about itself, such as its name, command, environment prefix and root marker |
| `deps_fragment` | The one reader of a `sushistack.deps.toml` fragment |
| `errors` | `SushiCoreError`, `ConfigError` and `DigestMismatchError`, the failures an entry point prints as one line |

### Printing

| Module | Owns |
| --- | --- |
| `config` | `load_appearance`: the `[cli]` table and the `SUSHI_CLI_*` variables resolved into one `AppearanceSpec` |
| `theme` | `Theme`, the style tokens, and the presets `default`, `mono` and `muted` |
| `icons` | `IconSet`, the prefix printed before a line, and the presets `text`, `emoji`, `minimal` and `none` |
| `renderer` | The `Renderer` protocol and its three backends: `RichRenderer`, `PlainRenderer`, `JsonRenderer` |
| `events` | The event kinds `JsonRenderer` writes and `event_line`, their one serialisation |
| `console` | `Console`, the facade a CLI calls: `info`, `success`, `warn`, `error`, `command`, `header`, `fail_panel`, `table`, `progress`, `result`, `prompt` |
| `cli_console` | `LazyConsole`, which builds the console on first use so `--help` runs outside a checkout |
| `markup` | `escape_unknown_tags`, which keeps a bracket as text unless it names a style |
| `terminal_background` | `is_dark_background`, decided from the `background` setting and `COLORFGBG` |
| `windows_console` | `enable_virtual_terminal` for a classic Windows console |
| `brand` | The Sushi Systems mark and wordmark as palettes and pixel grids |
| [`ui`](../../sushicore/ui/README.md) | One file per terminal element, each drawn from a `Theme` |
| [`help`](../../sushicore/help/README.md) | A help screen as data and the page that lays it out |
| `typer_help` | `help_group`, which wires the help page into a Typer application |
| `typer_theme` | `apply_typer_theme`, which recolours Typer's own help screen |

`build_console` in `sushicore/__init__.py` wires the printing modules together from the config
files a CLI hands it.

### Building

| Module | Owns |
| --- | --- |
| `proc` | `Runner`, which spawns a child process for a CLI |
| `build_env` | The environment a build runs under, with the vcvars snapshot on Windows |
| `cmake_cache` | What a `CMakeCache.txt` says about how its tree was configured |
| `cmake_driver` | `CMakeDriver`, the cmake and ctest command lines |
| `toolchain_args` | The compiler and vcpkg prefix arguments of a configure |
| `discovery` | `ExecutableIndex`, the built executables under a build tree |

### The surfaces every CLI registers

| Module | Owns |
| --- | --- |
| `root_options` | `--version` and `--describe` |
| `describe` | The command catalogue `--describe` prints as JSON |
| `diag`, `diag_commands` | `Diagnostics` and the `config` and `env` commands registered from it |
| `aliases` | `AliasTable`: old spellings that still run, hidden, and name their replacement |
| `entry` | `run`, the entry point that turns a `SushiCoreError` into one line and exit code 1 |
| [`provision`](../../sushicore/provision/README.md) | The dependency root, the registry, the doctor and the commands `setup`, `doctor`, `link`, `unlink` |

## Rules the code keeps

- `Console` talks to the `Renderer` protocol and never to Rich. A renderer is any object with
  the protocol's eight methods (`line`, `command`, `header`, `panel`, `table`, `progress`,
  `result`, `prompt`) and its `raw` property.
- `Theme` and `IconSet` are data. A new preset is registered with `register_theme` or
  `register_icon_set`; no other module changes.
- A component in `ui` reads `Theme` and `brand` and nothing else. `tests/test_ui_architecture.py`
  fails when one imports more.
- `typer_help` is the only module that imports Typer when it is loaded. `typer_theme`,
  `root_options`, `diag_commands` and `provision/commands.py` import it inside the function that
  needs it, and `aliases`, `describe` and `entry` only for type checking, so `import sushicore`
  works without the `typer` extra.
- Inside `provision`, lower layers do not import higher ones; the layer table is in
  [`docs/design/PROVISION.md`](../design/PROVISION.md).

The import cycles that break these rules today are listed in
[Known issues](../reference/KNOWN_ISSUES.md).

## Why each module is shaped as it is

The source files cite this section instead of carrying the reasoning themselves.

### The package

`sushicore` holds two things. The first is a config-driven presentation layer: `build_console`
assembles a `Console` from layered TOML config and the environment, using the `theme` and
`icons` presets and one `renderer` backend. The second is the build machinery that decides what
reaches a compiler in five of the consuming repositories: `proc.Runner` spawns, `cmake_cache`
reads `CMakeCache.txt`, `cmake_driver.CMakeDriver` writes the cmake and ctest invocations, and
`toolchain_args` derives the compiler and the vcpkg prefix. Each consumer's own
`services/project.py` keeps its build policy and calls into these. Each piece can be
registered, overridden or swapped on its own.

### `build_env`

A parent process cannot `call vcvars64.bat` and inherit the result: the batch file sets its
variables in its own shell, which then exits. So the shell runs as a child, its environment is
dumped and parsed, and that dictionary is handed to every cmake and ctest subprocess. The
snapshot is cached on disk, keyed by the configuration that produced it, so an unchanged config
skips the shell.

The primitives in the file are the parts that are the same wherever this is done.
`StackBuildEnv` composes them the way a module that consumes the shared toolchain needs.
SushiRuntime selects a toolchain instead of consuming one, and composes the primitives itself.

`RUNTIME_DEVICE_VARS` names the variables that pick which accelerator a program runs on. The
snapshot dumps the whole environment of the shell that produced it, so a variable exported for
one debugging session would be frozen into the cache and replayed into every later build and
run. A fresh terminal would not escape it, because the snapshot is merged over the current
environment. These variables name a run-time choice and never a toolchain fact, so they are
dropped when the cache is written and again when it is read.

`tests/test_build_env.py` guards both sides. The defect behind
`test_a_cache_written_before_this_existed_heals_on_read` was a snapshot taken while a session
had pinned SYCL to the CPU: it kept pinning every later build and run, from any terminal,
because the cache is merged over the current environment.
`test_the_current_environment_still_reaches_a_subprocess` checks the other side. Dropping the
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
outside a checkout still failed while the other four worked. That is the argument for the
module: with one console lifecycle, no CLI can be the one that missed it.

### `cmake_driver`

`CMakeDriver` knows the shape of a cmake command line. It does not know the name of a single
cache variable: which `-D` flags a module passes, which targets it has and which suites it runs
are policy, and policy stays in the module. Everything specific to a module arrives as a
parameter: `expect` for the cache entries a tree must already agree with, `targets` for what to
build, `label_regex` for which tests to select.

`configure` deletes `CMakeCache.txt` first when the tree was configured with a C++ compiler at
another path than the one the argv names. CMake would otherwise delete the cache itself and
run the configure a second time without the `-D` values of the command line, which leaves a
tree with default options: targets go missing and the build type is lost. This happens to
every build tree after the dependency root moves. The comparison ignores case and separators
as the platform does, and an argv that names no compiler leaves the cache alone.

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
repository. The split keeps the shared seam free of any domain and removes the tool-path
duplication the three repositories had.

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

A fragment is one table per dependency, keyed by its name, and a reserved `[module]` table that
carries metadata instead of a dependency. Several CLIs read the format, so it is read here
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

`config_show` marks a config file as `(found)` or `(absent)` in parentheses. Every CLI used to
write `[found]`, and Rich parsed it as a style tag and dropped it, so the marker was invisible
in all four.

### `discovery`

Every Sushi CLI has to answer the same question, "which of the files under `build/` is a
program I can run?", and every one of them answered it with its own copy of this walk. The
copies drifted in one place: which sibling directories to skip, because a module that builds a
dependency in-tree must not offer that dependency's executables as its own.

So the walk lives in `discovery` and the skip list is the caller's, supplied once when it
builds an `ExecutableIndex`. Nothing else about the search is configurable, on purpose:
`sr run`, `se run`, `sa run` and `sb run` should not be able to disagree about what counts as
an executable.

Shared objects on Linux come as `*.so` and as versioned names such as `*.so.1`. The suffix
check misses the versioned ones, so the walk matches the substring `.so`.

`ExecutableIndex.select` imports Rich's prompt and table inside the method. `find` and `match`
run on every `run` and must not pay for importing Rich's table machinery.

### `module_config`

Every Sushi CLI is installed outside the repository it builds, because pip or pipx puts it in a
venv, so the package's own location says nothing about where the project lives. The invocation
directory does. Each CLI therefore walks up from the working directory looking for one of its
markers: the checkout's marker file, or the release manifest an unpacked binary install
carries. It then layers `config.toml`, the workspace-shared `config.local.toml` that
`hub install` writes, and the repository's own `config.local.toml`, in that order.

That is the same procedure five times over. It differs only in the marker, the project's name
in the error message and the prefix on the environment overrides, and a `ModuleProfile` already
states all three.

### `profile`

The CLIs (hub, sr, se, sa, sb and sd) differ from each other in a handful of facts: a display
name, the command a user types, the prefix on their environment overrides, the file that marks
a project root, and which sibling checkouts they build in-tree. Everything else about locating
a project, layering config, listing executables and reporting diagnostics is the same work.

Those facts used to be spelled out separately in each CLI's `config.py`, `console.py`,
`services/discovery.py` and `services/diag.py`, so a module was described four times and could
disagree with itself. A `ModuleProfile` is the one place a module describes itself, and the
shared machinery reads it.

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
`docs/design/HUB.md` fixes.

### `stack_config`

SushiEngine, SushiAI and SushiBLAS are heads of the stack: they select no SYCL toolchain of
their own and consume the one `setup` or `hub install` provisions into a dependency root.
Resolving the compiler and vcpkg from those roots is identical work in all three, and each
carried its own copy of it.

SushiRuntime is not a subclass, by decision. It owns the bundle instead of consuming it,
selects between toolchains (acpp, clang++, icpx) and resolves dependencies with a different
signature. Forcing it into this shape would bend the base class around a case it does not
describe.

### `theme`

`rule_line` styles the dashes either side of a `console.rule()` title and, through Rich's
theme-wide `rule.line` key, anything else that asks for that style. Its value `default` means
the terminal's own foreground colour: white on a dark terminal, black on a light one. A fixed
colour would be chosen without knowing the user's background.

`as_rich_styles` also sets the `bar.*` and `progress.*` keys. The built-in columns of
`rich.progress.Progress` (`SpinnerColumn`, `BarColumn` and the `[progress.*]` `TextColumn`
templates) read those theme keys directly. Overriding them themes `rich.progress.track()` and
any bare `Progress(...)` in a downstream CLI with no change at the call site.

The preset registered as `default` and `sushiweb` is lifted from the palette in sushiweb's
`src/styles/global.css`. It is
near-monochrome, grey text on near-black or near-white, with a single amber accent (`#f0a500`)
in place of the many hues of a terminal default. The semantic colours are desaturated to sit
beside that accent instead of competing with it. The accent is reused for header rules and for
inline commands, as the site uses one accent for everything.

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
environment variables win. That plumbing used to be copied into each repository's `config.py`;
it lives in `workspace` so there is one seam.

The module knows nothing about SYCL, toolchains or any module's schema. It only locates
directories and merges the TOML the caller hands it. Each CLI keeps its own `Config` dataclass
and passes in its markers, section name and environment-variable map.

`LEGACY_SHARED_CONFIG` is where `hub install` wrote the shared tool paths before 2026-09-22,
relative to the workspace root. It is read as a fallback so a workspace that no `hub` command
has upgraded yet still resolves.
