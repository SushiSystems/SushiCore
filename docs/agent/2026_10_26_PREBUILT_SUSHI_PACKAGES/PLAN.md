# Prebuilt Sushi packages Implementation Plan

**Status:** Open — 2026-10-26; SushiCore side coded, repository tasks open

**Goal:** A consumer's CLI gets a package for every Sushi library of its chain, builds a missing
one once through the library's own CLI, and reuses it afterwards.

**Architecture:** One sub-package of small files under `sushicore/provision/sushi_packages/`,
lower layers first, then the fragment keys, the settings wiring and the shared `package`
command. The library and consumer repositories follow as orchestrator tasks.

**Tech Stack:** Python 3.10+, standard library only, pytest.

**Spec:** `docs/agent/2026_10_26_PREBUILT_SUSHI_PACKAGES/SPEC.md`. Its decisions R1 to R11, D1 to D19 and P1 to P9 hold here.

## Global Constraints

- No new dependency. The processes the code starts are the library CLI, git and the configured
  cmake, each behind an injected callable, and no test starts one.
- One class per file. Every error derives from `PackageError`, which derives from `SushiCoreError`.
- A file opens with the five licence lines and a module docstring; every function, class and
  test carries a one-sentence docstring that starts with its verb. Lines are 100 columns, strings
  double-quoted, constants `K_UPPER_SNAKE`, no import inside a function of the source.
- Never run `se`, `cmake`, `ninja` or `ctest`. The verification of a SushiCore task is its pytest
  command; the closing task runs `tools/check_all.py`. The tasks of other repositories are
  verified by the owner's build.
- Tests mirror the source: `tests/provision/sushi_packages/test_<file>.py`.
- A task lands with its README row, its documentation and its changelog line under
  `## Unreleased` in `docs/reference/CHANGELOG.md`.

## The shape coded (R10)

| Unit | Shape |
| --- | --- |
| `ClosureWalk` | Takes `ISourceLocator` and a fragment reader through its constructor; returns `LibraryNode`s, dependencies first, each once; owns cycle detection and the pin versions |
| `PackageResolver` | Takes `ClosureWalk`, `KeyFactory`, `PackageStore`, `IPackageBuilder`, `ForcedPackages`, `PackageLocks`, `LinkPublisher` and a report callable; its per-call state is a private dataclass, not a collaborator |
| `ISourceLocator` | `locate(root, name, version, configured)`; `SushiSourceLocator` wraps `sushi_sources.resolve` |
| `ResolvedPackage` | `package`, `key` (None for a forced package), `built`, `seconds`, `link` |
| `CompilerCheck` | `verify(build_tree, expected)`, called before the build and before the install |
| `PackageEnvironment` | Assembles the environment of spec section 6; the builder receives it |
| `Package` | Owns `config_folder()`, `run_dirs(platform)` and `below()` |
| `PackageStore` | Finds, stages, commits, touches and prunes; knows no links and no keys beyond the digest |
| `LinkPublisher` | Sets the consumer's link under the link lock; `protected(name)` lists the digests any link names |

## SushiCore tasks, in hierarchy order

All are done. Each has one acceptance line and one build, the pytest command named; "Docs" names
what the task updates besides its README row and changelog line.

| Id | Task and files | Acceptance | Build | Docs |
| --- | --- | --- | --- | --- |
| S1 | `deps_fragment.py`: `Fragment.cli`, `Fragment.package_exclude` | A fragment with both keys reads both; one without reads them empty; a number or a list of numbers raises naming the key | `python -m pytest tests/test_deps_fragment` | `DEPENDENCY_FRAGMENT.md` |
| S2 | `package_error.py`, `package_key.py` | Equal parts give one digest; each of the eight parts changed gives another; the order of `below` does not matter | `python -m pytest tests/provision/sushi_packages/test_package_key.py tests/provision/sushi_packages/test_package_error.py` | none |
| S3 | `source_state.py` | The hash ignores `docs/`, `*.md`, `build/` and `build-*/`; it changes for a changed, new or deleted source file; `package_exclude` entries are left out | `python -m pytest tests/provision/sushi_packages/test_source_state.py` | none |
| S4 | `configure_inputs.py` | Local config, `vcpkg.json`, `vcpkg-configuration.json`, vcpkg HEAD, triplet and CMake minor version each change the hash; a patch version does not | `python -m pytest tests/provision/sushi_packages/test_configure_inputs.py` | none |
| S5 | `toolchain_identity.py` | One `--version` text gives one identity, another gives another, a stamp tag is joined, a failing compiler raises | `python -m pytest tests/provision/sushi_packages/test_toolchain_identity.py` | none |
| S6 | `compiler_check.py` | A tree of another compiler raises naming both identities; an unconfigured tree passes with one warning | `python -m pytest tests/provision/sushi_packages/test_compiler_check.py` | none |
| S7 | `build_tree.py` | `pkg-<12 hex>`, stable for equal input, another for another build type, options or toolchain | `python -m pytest tests/provision/sushi_packages/test_build_tree.py` | none |
| S8 | `package.py` | The config folder keeps the library's case; `run_dirs` is `bin` on Windows and the existing `lib` and `lib64` elsewhere; an install without a config raises | `python -m pytest tests/provision/sushi_packages/test_package.py` | none |
| S9 | `package_locks.py` | The three lock files have the documented names; checkout, key, link in that order passes and any reverse order raises | `python -m pytest tests/provision/sushi_packages/test_package_locks.py` | none |
| S10 | `stable_link.py` | The Windows link, a junction, follows the newest of two packages and keeps both folders; the posix link is swapped by rename and leaves no `.new`; `targets` lists every digest a link names | `python -m pytest tests/provision/sushi_packages/test_stable_link.py` | none |
| S11 | `package_store.py` | A folder without a stamp is not found; a rename that fails once is retried; prune keeps `package_keep` by last use and spares protected digests and digests a package of another library lists; a deletion goes through `.trash`; a rename that fails is skipped with one warning; a fresh `.partial` stays and a day-old one goes; a keep below 1 raises | `python -m pytest tests/provision/sushi_packages/test_package_store.py` | none |
| S12 | `link_publisher.py` | The published link reaches the package; the links of two consumers protect two digests, and one moves on republish | `python -m pytest tests/provision/sushi_packages/test_link_publisher.py` | none |
| S13 | `package_environment.py` | The environment holds the compiler, one `<NAME>_PACKAGE` per package, the marker and no `_DIR` entry; a parent's package variable for another library is dropped | `python -m pytest tests/provision/sushi_packages/test_package_environment.py` | `CONFIGURATION.md` |
| S14 | `forced_packages.py` | Without the marker a variable is ignored with one warning; with it the package is taken; another toolchain or build type, and a digest not in the store, raise | `python -m pytest tests/provision/sushi_packages/test_forced_packages.py` | none |
| S15 | `package_builder.py` | The build and package commands of spec section 4 run in order in the checkout; a failed build runs no install; the compiler check runs before the first command | `python -m pytest tests/provision/sushi_packages/test_package_builder.py` | none |
| S16 | `key_factory.py` | The key composes every part; another SushiCore version gives another digest; the compiler is probed once; a docs-only difference leaves the digest | `python -m pytest tests/provision/sushi_packages/test_key_factory.py` | none |
| S17 | `package_request.py`, `library_node.py`, `source_locator.py` | The configured directory wins over the sibling; no checkout raises naming `<NAME>_DIR`; the records are frozen with the documented defaults | `python -m pytest tests/provision/sushi_packages/test_source_locator.py tests/provision/sushi_packages/test_package_request.py tests/provision/sushi_packages/test_library_node.py` | none |
| S18 | `closure_walk.py` | The diamond lists SushiRuntime once, before SushiBLAS; a cycle raises naming the trail; the consumer's pin decides the version; a malformed fragment is a package error | `python -m pytest tests/provision/sushi_packages/test_closure_walk.py` | none |
| S19 | `package_set.py` | `lines()` gives `reused` or `built ... in <s>s`; `definitions()` gives `-D<Package>_DIR` for every package with the library's case; `run_dirs` lists every package | `python -m pytest tests/provision/sushi_packages/test_package_set.py` | none |
| S20 | `package_choices.py`, `package_resolver.py` | The diamond resolves one runtime package; a changed runtime source gives BLAS a new key; a docs-only difference gives none; a second run reuses all and builds nothing; one library at two keys raises `PackageConflictError` naming both digests and both choosers; no `cli` with no package raises naming the fragment; a failed build leaves no `.partial`; a stale variable is ignored; a forced package of another build type is refused | `python -m pytest tests/provision/sushi_packages/test_package_resolver.py tests/provision/sushi_packages/test_package_choices.py` | none |
| S21 | `default_resolver.py`, `sushi_packages/__init__.py` | The package exposes exactly the documented names; assembling the resolver starts no process; the keep count is 3, a configured value, or the variable; a bad variable raises | `python -m pytest tests/provision/sushi_packages/test_default_resolver.py` | provision `README.md` section "Sushi libraries as packages", `OVERVIEW.md`, `FAQ.md` |
| S22 | `provision/config.py`: `package_keep`; `stack_config.py`: `sushi_packages`, `sushi_definitions(root, packaged)` | The keep count defaults to 3; `sushi_definitions` skips a packaged library and keeps the others; the request carries owner, compiler, build type, options and configured directories | `python -m pytest tests/test_stack_config.py tests/provision/test_config.py` | `CLI_INTEGRATION.md`, `CONFIGURATION.md` |
| S23 | `package_install.py`, `package_command.py` | A built tree is installed with its own build type and marked; an unbuilt tree exits 1 naming it; `--no-archive` runs no CPack; a foreign prefix needs `--force`; a staged one does not; the checkout is never the prefix; the registered command installs `build` into `build/dist` | `python -m pytest tests/provision/test_package_install.py tests/provision/test_package_command.py` | `CLI_INTEGRATION.md`, provision `README.md` |
| S24 | Closing check: `tools/layering/check_package_layers.py` gains the layers of the new files; this folder's status | `python tools/check_all.py .` prints `clean` | `python tools/check_all.py .` | none |

## Orchestrator tasks, outside SushiCore

Each task lands with the documentation and changelog line of its repository: the CLI's README
for a new flag or command, the repository's `docs/reference/CHANGELOG.md`, and a status line if
a design page names the dependency. Every library CLI task shares one contract: `build` takes
`--build-dir <path>` and `--lean`, the CLI honours `SUSHISTACK_CXX` over its configured
compiler, and `package` is `register_package_command` from SushiCore. Each consumer CLI calls
`cfg.sushi_packages`, prints `lines()`, appends `cfg.sushi_definitions(root, packages)` and
`packages.definitions()` to its configure and prepends `packages.run_dirs(cfg.platform)` with
`build_env.prepend_path`. Generated headers: none of SushiLog, SushiProfiler, SushiRuntime and
SushiBLAS writes one (P6); their package files are install-tree only.

| Id | Repository | Change | Acceptance |
| --- | --- | --- | --- |
| O1 | SushiLog | New `cli/sushistack.deps.toml` with `[module]`, `cli = "sl"`, `depends_on = []`; `package` and the build contract in the CLI | `sl build --build-dir build/pkg-x --lean`, then `sl package --build-dir build/pkg-x --prefix <p> --no-archive` leaves `SushiLogConfig.cmake` under `<p>/lib/cmake/SushiLog` |
| O2 | SushiProfiler | The same with `cli = "sp"` | The same for `SushiProfiler` |
| O3 | SushiRuntime | `cli = "sr"` under `[module]` of `cli/sushistack.deps.toml`; the build contract; `sr package` takes `--build-dir` and keeps its CPack and stage marker; the CLI calls `sushi_packages` for SushiLog and, once its fragment names it, SushiProfiler. **P1:** new `cmake/SushiRuntimeSycl.cmake.in` that sets `SushiRuntime_SYCL_TOOLCHAIN` to `@SR_SYCL_TOOLCHAIN@` and gives the toolchain's `add_sycl_to_target` (AdaptiveCpp: `find_package(AdaptiveCpp REQUIRED)`; oneAPI: `find_package(IntelSYCL REQUIRED)`; intel-llvm: the `IntelSYCL::SYCL_CXX` stub and an empty `add_sycl_to_target` when none exists), the logic of `cmake/Sycl.cmake` lines 120 to 180; `cmake/SushiRuntimeInstall.cmake` gains `configure_file("${SR_CMAKE_DIR}/SushiRuntimeSycl.cmake.in" "${PROJECT_BINARY_DIR}/SushiRuntimeSycl.cmake" @ONLY)` after line 56 and the file in the `install(FILES` of line 71; `cmake/SushiRuntimeConfig.cmake.in` lines 23 to 36 (the comment and the two `IntelSYCL` blocks) become `include("${CMAKE_CURRENT_LIST_DIR}/SushiRuntimeSycl.cmake")`; `cmake/Dependencies.cmake` lines 31 to 48 become the log block below | `sr build` configures with `find_package(SushiLog CONFIG REQUIRED)` and compiles no SushiLog source; the installed `SushiRuntimeConfig.cmake` defines `SushiRuntime_SYCL_TOOLCHAIN` |
| O4 | SushiBLAS | `cli = "sb"`; the build contract; `package`; the CLI calls `sushi_packages` for SushiRuntime and SushiLog. **Header modules:** `CMakeLists.txt` line 153 `install(FILES` gains `"${CMAKE_CURRENT_SOURCE_DIR}/cmake/SushiBLASHeaderModules.cmake"` and `cmake/SushiBLASConfig.cmake.in` gains `include("${CMAKE_CURRENT_LIST_DIR}/SushiBLASHeaderModules.cmake")` before line 50 `check_required_components`. **P1:** `cmake/SyclTarget.cmake` lines 81, 149, 172 and 192 read `SushiRuntime_SYCL_TOOLCHAIN` in place of `SR_SYCL_TOOLCHAIN`, and the comment at `CMakeLists.txt` line 30 follows. `cmake/Runtime.cmake` lines 6 to 41 become the runtime block; `cmake/SushiBLASSushiLog.cmake` lines 7 to 28 become the log block | `sb build` links the SushiRuntime package and compiles no runtime source; `find_package(SushiBLAS CONFIG)` on the installed prefix defines `SushiBLAS::Geometry` |
| O5 | SushiAI | The CLI calls `sushi_packages` for SushiRuntime, SushiBLAS and SushiLog. `cmake/Runtime.cmake` lines 6 to 57 become the runtime block; `cmake/BLAS.cmake` lines 6 to 39 the BLAS block; `cmake/Log.cmake` lines 6 to 25 the log block; **P1:** `cmake/SushiAISyclTarget.cmake` lines 21, 25 and 38 read `SushiRuntime_SYCL_TOOLCHAIN` | `sa build` compiles only SushiAI sources, and a test binary starts with the package directories on the path |
| O6 | SushiDSP | The CLI calls `sushi_packages` for SushiLog; `CMakeLists.txt` lines 29 to 36 become the log block | `sd build` has no SushiLog source in its tree |
| O7 | SushiTrack | The CLI calls `sushi_packages` for SushiLog; `cmake/SushiTrackSushiLog.cmake` line 7 (the comment) and lines 12 to 26 become the log block; the `SUSHITRACK_ENABLE_LOGGING` option stays | `st build` has no SushiLog source in its tree |
| O8 | SushiEngine (the other session's) | `cli/sushiengine/configure.py` line 117 calls `sushi_packages` for SushiRuntime, SushiBLAS and SushiLog. `cmake/SushiLog.cmake` lines 6 to 26 become the log block; `cmake/Runtime.cmake` lines 6 to 79 the runtime block; `cmake/BLASLibrary.cmake` lines 14 to 30 the BLAS block; in the runtime lane of `cmake/BLAS.cmake` the `include("${SUSHIBLAS_DIR}/cmake/SushiBLASHeaderModules.cmake")` line goes, the package config including it, and `sushiblas_declare_header_modules()` stays; the native lane keeps the include (D14). **P1:** `cmake/SyclTarget.cmake` lines 47, 69, 109 and 112 and the comment at `CMakeLists.txt` line 61 read `SushiRuntime_SYCL_TOOLCHAIN` | The runtime lane builds with no SushiRuntime or SushiBLAS source in its tree |

### CMake blocks

The log block, for `SushiLog.cmake` of SushiEngine, `Log.cmake` of SushiAI,
`SushiBLASSushiLog.cmake`, `SushiTrackSushiLog.cmake`, `Dependencies.cmake` of SushiRuntime and
the SushiDSP root file:

```cmake
# SushiLog, the one logger of the process. The CLI builds or reuses its package and passes
# SushiLog_DIR; nothing is built in this tree and nothing is downloaded.
find_package(SushiLog CONFIG REQUIRED)
message(STATUS "Found SushiLog ${SushiLog_VERSION}: ${SushiLog_DIR}")
```

The runtime block, for SushiBLAS, SushiAI and SushiEngine:

```cmake
# SushiRuntime as a package. The CLI builds or reuses it and passes SushiRuntime_DIR.
find_package(SushiRuntime CONFIG REQUIRED)
message(STATUS "Found SushiRuntime ${SushiRuntime_VERSION}: ${SushiRuntime_DIR}")
```

The BLAS block, for SushiAI and SushiEngine:

```cmake
# SushiBLAS as a package. The CLI builds or reuses it and passes SushiBLAS_DIR.
find_package(SushiBLAS CONFIG REQUIRED)
message(STATUS "Found SushiBLAS ${SushiBLAS_VERSION}: ${SushiBLAS_DIR}")
```

## The owner's builds

One build per repository, in dependency order. Each has its own acceptance and the owner runs
them with the thread count he names.

| Id | Build | Acceptance |
| --- | --- | --- |
| B1 | SushiLog: `sl build`, `sl package --build-dir build/pkg-x --prefix <p> --no-archive` | The package config exists under `<p>` |
| B2 | SushiProfiler: `sp build`, `sp package` | The same |
| B3 | SushiRuntime: `sr build` | The first run prints `sushilog: built`, the second `sushilog: reused`; the SushiLog source is not in the runtime's tree |
| B4 | SushiBLAS: `sb build` | It prints `built` for SushiLog and SushiRuntime once and compiles no runtime source. A docs-only commit in SushiRuntime then prints `reused` for both. A `.cpp` change in SushiRuntime prints `built` for SushiRuntime, compiles that one unit there, and `ninja -d explain` in SushiBLAS's `build/pkg-*` tree lists no `.cpp` object dirty; the installed header timestamps equal the source's; the reconfigure after the changed `*Targets.cmake` is visible |
| B5 | SushiAI: `sa build` and a test binary | The binary starts with only the package directories on the path; the SushiBLAS and SushiRuntime packages are the ones its closure chose |
| B6 | SushiDSP: `sd build` | No SushiLog source in its tree |
| B7 | SushiTrack: `st build` | No SushiLog source in its tree |
| B8 | SushiEngine, the other session's build | The runtime lane has no SushiRuntime or SushiBLAS source in its tree |

If B4 shows that `cmake --install` does not keep file timestamps, the stable link of D7 does not
avoid the recompile after a runtime change, and the design needs a second look.

## Review Focus

1. The two-key refusal names both digests and both choosers (S20).
2. A folder without a stamp is never used, and a `.partial` of another process is never deleted
   inside its first day (S11).
3. No prune touches a package of the closure being resolved or one a link names (S11, S20).
4. Lock order: checkout, key, link (S9, S20).
5. A docs-only difference does not change a key (S3, S20).
6. The posix branch of the link swap was not run on Windows (S10): its test skipped.
