# Prebuilt Sushi packages

**Status:** Open — 2026-10-26; SushiCore side coded, repository tasks open

Every Sushi library is consumed as a built, installed package and never as a subdirectory of the
consumer's build tree. The owner's report: SushiRuntime is compiled again in the build tree of
SushiEngine, SushiBLAS and SushiAI, and build times grow with each consumer.

## 1. Decisions

R1 to R11 are the orchestrator's rulings of 2026-10-26. D1 to D19 and P1 to P9 are decisions this document
takes where the rulings are silent; each has its reason in one line.

| Id | Decision |
| --- | --- |
| R1 | Consumers are in scope: SushiRuntime, SushiBLAS, SushiAI, SushiDSP and SushiTrack. SushiEngine is another session's work and gets the exact lines in the plan. A consumer calls `find_package(<Name> CONFIG REQUIRED)` and has no `add_subdirectory` and no `QUIET` fallback for a library the CLI hands as a package. `sushi_definitions` stops emitting `-D<NAME>_DIR` for a packaged library. A `_DIR` value reaches CMake only as a `-D` cache entry and never through the environment, because a Windows environment is case-insensitive and `SUSHIRUNTIME_DIR` collides with `SushiRuntime_DIR` |
| R2 | SushiLog and SushiProfiler get a `cli/sushistack.deps.toml` with `[module] cli`. The fragment reader gains the `cli` field |
| R3 | One shared `package` command in SushiCore, registered by every library CLI. It takes the build tree, `--no-archive` and `--force`. `sr package` keeps CPack for distribution |
| R4 | State of the files is in section 12. SushiRuntime does not consume SushiProfiler yet; the closure gains it by itself when its fragment names it. SushiBLAS already has an export set. The real SushiBLAS gap is that `cmake/SushiBLASHeaderModules.cmake` is not installed. There is no hwloc gap: the runtime is a shared library and hwloc is not in its exported interface |
| R5 | The resolver returns each package's run-time directories, `bin/` on Windows and `lib/` on Linux. The consumer CLI prepends them with `build_env.prepend_path` |
| R6 | A package is built in one tree per configuration identity, `build/pkg-<short of build type, options digest, toolchain>`, and not per key. A source change rebuilds incrementally in that tree. The developer's `build/` is never touched. Package builds turn tests, examples and benchmarks off. `package` installs from that tree |
| R7 | Key rules are in section 3: content hash without `docs/` and `*.md`, configure inputs, the consumer's compiler checked before the build, the vcpkg and CMake versions |
| R8 | Store rules are in section 5: two locks, reuse after the lock, retried rename, no deletion of another process's `.partial`, delete by rename, prune by last use |
| R9 | A `<NAME>_PACKAGE` variable is honoured only beside the marker the builder sets for nested calls; a stale one is ignored with a warning |
| R10 | The draft's shape is fixed in the plan: collaborators through constructors, an injected source locator, an optional key on a resolved package, a compiler check class, an environment assembly class apart from the builder, the config-folder lookup in the package, no dead code, no import inside a function |
| R11 | The plan follows the hierarchy, gives each task one acceptance line and one build, and puts documentation and changelog inside the owning task |
| D1 | The source part of the key is a content hash and never a commit. A docs-only commit must not change it, and a commit hash would |
| D2 | The consumer's compiler reaches the library CLI as the environment variable `SUSHISTACK_CXX`, which the CLI honours over its config. A flag would need a different spelling in four CLIs |
| D3 | One recipe flag, `--lean`, on every library CLI's `build`: no tests, examples or benchmarks. Its name and meaning are the contract, and the key carries the recipe name `lean-1`, so a changed meaning is a new key |
| D4 | `build` also takes `--build-dir <path>`; without it, it builds `build/` as today |
| D5 | Per-library options come from the caller, which passes them to `sushi_packages`. SushiCore adds no config table. A consumer CLI maps its own flags, such as `--distributed`, to the options of the library they belong to |
| D6 | A library with no `cli` in its fragment and no package in the store is refused. There is no fallback to a subdirectory, so one rule holds for every library |
| D7 | Each consumer receives its own stable path, `<home>/packages/<name>/@<config short>-<consumer name>`: a directory junction on Windows (no administrator rights), a symlink on Linux. The resolver sets it to the chosen digest on every resolution, reuse included, so the include paths in the consumer's flags do not change when a library's source changes and the consumer recompiles only what the changed files reach. One link per consumer means two consumers of different source states never move each other's link |
| D8 | A package's `prefix/` holds what `package` installed. Run-time directories are `bin/` on Windows and `lib/` or `lib64/` on Linux, whichever exist |
| D9 | The package command runs `cmake --install <tree> --prefix <prefix>`, and CPack only when `--no-archive` is absent. The `cmake --version` probe for the key runs the cmake the consumer's config names, through a probe the resolver's assembly passes in |
| D10 | A forced package whose stamp has another toolchain or build type is refused, naming both. A forced package whose digest is not in the store is refused |
| D11 | Lock order is checkout lock, then key lock, then link lock, always. A task that needs another order is a defect |
| D12 | The pinned `commit` of a fragment is no longer part of the key. `doctor` still checks it. A fetched copy is a clean checkout of that commit, so its content hash is the commit's |
| D13 | `package_exclude` is a second `[module]` key, a list of git pathspecs added to the default exclusions of the source hash |
| D14 | SushiEngine's runtime lane consumes the packages. Its native lane, which has no SYCL compiler, keeps including `SushiBLASHeaderModules.cmake` from the checkout, because a SushiBLAS package cannot be built without one. The change for the native lane waits for a header-only SushiBLAS package, which this work does not make |
| D15 | `package` marks a prefix it staged with the file `.sushi_package_stage`: a prefix that holds files and no marker is cleared only with `--force`, and the prefix is never the checkout, one of its parents or a protected folder. The default prefix is `build/dist` and the default tree is `build` |
| D16 | `StackConfig.sushi_packages(root, build_type, options, report, warn, compiler)` returns a `PackageSet`; `StackConfig.sushi_definitions(root, packaged)` skips the libraries of `packaged`. A library whose `<name>_dir` config field is set reaches the resolver as the configured directory |
| D17 | A package a parent forced has no key and gets no consumer link; the nested build links it through its own prefix |
| D18 | The `inputs` part of the key is one hash of the configure inputs, so a changed input changes the digest without the stamp holding the inputs' content |
| D19 | `sushi_packages` is one layer of `provision` (`tools/layering/check_package_layers.py`), `package_install` is layer 1 and `package_command` layer 7, above `commands` |
| P1 | The SYCL policy travels with the runtime package. SushiRuntime installs `SushiRuntimeSycl.cmake`, which gives the toolchain result as `SushiRuntime_SYCL_TOOLCHAIN` and the `add_sycl_to_target` provision that `cmake/Sycl.cmake` gives today; `SushiRuntimeConfig.cmake` includes it. The consumers' SYCL files switch to it, so the runtime's toolchain is the one truth |
| P2 | The stable link is per consumer and is published by a `LinkPublisher` collaborator of the resolver. The store does not own the link |
| P3 | Prune never deletes a digest that any link points at, besides the chosen set and the `below` of kept packages |
| P4 | A link swap on Windows deletes the junction and creates it again under the link lock; the consumer's own build is the only reader of its link. On Linux the new symlink is created beside the old one and renamed over it. A `.trash` rename that fails is skipped with a warning and retried at the next prune |
| P5 | A `KeyFactory` composes the source hash, the configure inputs, the compiler identity and the `below` digests into a key |
| P6 | Generated headers of a library are written only when their content changes. A changed `*Targets.cmake` re-runs the consumer's configure step and costs no compile |
| P7 | The build-time table says reconfigure, relink or re-archive per target kind, read from each library's `add_library` |
| P8 | `CompilerCheck` probes the cached `CMAKE_CXX_COMPILER` with `--version`, so it compares identities of one kind |
| P9 | The key adds the SushiCore version, which is the recipe that drives the build, and the vcpkg triplet. The source hash always excludes `build/` and `build-*/`, whatever `.gitignore` says |

## 2. What is built

| Repository | Change |
| --- | --- |
| SushiCore | The sub-package `sushicore.provision.sushi_packages`; the `cli` and `package_exclude` keys of the fragment; `StackConfig.sushi_packages` and a `sushi_definitions` that skips packaged libraries; `ProvisionSettings.package_keep`; the shared `package` command |
| SushiLog, SushiProfiler, SushiRuntime, SushiBLAS | A fragment with `cli`; the `package` command; `build --build-dir` and `--lean`; `SUSHISTACK_CXX` honoured |
| SushiBLAS | The header-modules file installed with the package |
| SushiRuntime, SushiBLAS, SushiAI, SushiDSP, SushiTrack, SushiEngine | `find_package(... CONFIG REQUIRED)` in place of the subdirectory; the CLI calls `sushi_packages` |

## 3. Resolution and the key

`PackageResolver.resolve` takes the consumer's checkout, its compiler and its build type. It
reads the consumer's fragment, follows `[module] depends_on` through each library's own fragment
and resolves the libraries bottom-up: a library is resolved after every library it depends on.
The checkout of a library is found as today: `<NAME>_DIR`, the sibling, then the fetched copy.
The result is a `PackageSet`: one `ResolvedPackage` per library, in dependency order.

The key has these parts, hashed with SHA-256 over canonical JSON:

| Part | Value |
| --- | --- |
| `name` | The library's lower-case name |
| `source` | The hash of the content of every tracked file and every untracked, not ignored file, by path and bytes, without `docs/`, `*.md`, `build/`, `build-*/` and the paths of `package_exclude` |
| `toolchain` | The SHA-256 of the compiler's `--version` output, joined with the tag of its toolchain stamp when the install has one |
| `build_type` | `release`, `debug`, `relwithdebinfo` or `asan`, lower case |
| `options` | The resolved extra arguments of the library's `build`, in order |
| `recipe` | `lean-1`, with the SushiCore version |
| `inputs` | The hash of the library's `cli/config.local.toml`; the hash of its `vcpkg.json` and `vcpkg-configuration.json` with the HEAD of the vcpkg tree the consumer uses and its triplet; the CMake major and minor version |
| `below` | The key digests of the Sushi packages this one was built against, by name |

`below` puts the chain in the key: the SushiBLAS key contains the SushiRuntime key, which
contains the SushiLog key and, when its fragment names it, the SushiProfiler key. A changed
SushiRuntime source gives SushiBLAS a new key, and a consumer never gets a SushiBLAS package
built against a runtime package other than the one it links itself.

The short form is the first 12 hex digits.

## 4. Building a missing package

The `cli` key of the library's `[module]` table names its CLI. The builder runs, in the library's
checkout, with the environment of section 6:

1. `<cli> build --type <build_type> --build-dir build/pkg-<id> --lean <options...>`
2. `<cli> package --build-dir build/pkg-<id> --prefix <store>/<name>/<digest>.partial/prefix --no-archive --force`

`<id>` is the first 12 hex digits of the hash of build type, options digest and toolchain. The
tree is reused by every later key of that configuration, so a source change compiles
incrementally. The developer's `build/` is not read or written.

The compiler check class runs `--version` on the `CMAKE_CXX_COMPILER` recorded in the tree's
`CMakeCache.txt` and compares that identity with the key's before step 1, when the tree exists, and again between the steps. A mismatch is
refused with a message naming both identities. The second check catches a CLI that ignored
`SUSHISTACK_CXX`; nothing is installed in that case.

## 5. The store

Packages live under `<home>/packages/<name>/<digest>/`: `prefix/`, the stamp
`package.stamp.json` and a `.used` file. The stamp records every key part, the digest, the
install time and the build seconds, and is written last: a folder without one is not a package.

- A library checkout lock, `<home>/packages/.locks/<name>-<hash of the checkout path>.lock`, is
  held while a build runs in that checkout. A key lock,
  `<home>/packages/.locks/<name>-<digest>.lock`, is held while that key is installed. A link lock,
  `<home>/packages/.locks/<name>-link-<consumer>.lock`, is held while that consumer's link changes. All
  reuse `provision/lock.py`; the order is D11.
- After the key lock is taken, a final folder that exists is reused and nothing is built.
- An install goes into `<digest>.partial` and is renamed into place. The rename is retried with a
  short wait on Windows, where a scanner can hold the folder.
- A process never deletes a `.partial` folder it did not create, except a stale one: older than
  a day, removed under its key lock.
- A deletion renames the folder to `<digest>.trash` and then sweeps it. A rename or sweep that
  fails is skipped with a warning and retried at the next prune.
- Every resolution touches `.used` of each package it chose. After an install the store prunes
  that library to the `package_keep` most recently used packages (default 3, environment
  `SUSHISTACK_PACKAGE_KEEP`, a value below 1 refused) and never deletes a package that this run
  chose, that a kept package lists in its `below`, or that any consumer's link points at.
- The link of D7 is set on every resolution, reuse included, under the link lock. On Windows the
  junction is deleted and created again, because only the consumer's own build reads it. On Linux
  the new symlink is created beside the old one and renamed over it. The resolver does this through
  a `LinkPublisher`; the store knows nothing of links.

## 6. Environment of a build

`PackageEnvironment` assembles it and the builder only runs it: `SUSHISTACK_CXX`; one
`<NAME>_PACKAGE` per package already chosen below the library, holding its prefix; and the
marker `SUSHISTACK_PACKAGE_NESTED=1`. No `_DIR` variable is set.

A library CLI reads `<NAME>_PACKAGE` only when the marker is set (R9). Without it the variable
is ignored and one warning names it. With it the package is forced: its stamp is read, its
toolchain and build type are compared with the request (D10), and the packages its stamp says it
was built against are chosen with it. Two forced packages that name different digests for one
library are refused by the same two-key check as any other conflict.

## 7. What the consumer receives

- `-D<Package>_DIR=<config folder>` for every library of the closure, transitive ones included,
  because a package config loads its own dependencies with `find_dependency`. `<Package>` is the
  name of the folder under a `cmake` folder of the prefix that is named after the library, so the
  case is the library's own. The package owns that lookup.
- The run-time directories of every package (R5, D8), through the stable path of D7. The
  consumer CLI prepends them to `PATH` or `LD_LIBRARY_PATH`.
- One line per library per run: `<name>: reused <short>` or `<name>: built <short> in <s>s`.

## 8. Refusals

- A library with no `cli` and no stored package (D6).
- One library at two keys: the refusal names both digests and who chose each.
- A checkout that is not a git repository, a compiler with no identity, a compiler mismatch
  (section 4), a forced package of another toolchain or build type (D10).
- A lock that is not free within its timeout: the message names the holder.

A package built with another toolchain or build type is never used; its key differs, so it is
built again.

## 9. Build time

What rebuilds, by change. A library's own tree is its `build/pkg-<id>`.

| Change | SushiLog | SushiRuntime | SushiBLAS | SushiAI | Why this is the least |
| --- | --- | --- | --- | --- | --- |
| A commit that touches `docs/` and `*.md` only | nothing | nothing | nothing | nothing | The key hashes content without them, so each digest is unchanged and each package is reused. A key on the commit would rebuild the whole chain |
| A `.cpp` change in SushiRuntime | nothing | that unit and the link of the shared library, once, in its own tree | re-keyed; reconfigures, because the installed `SushiRuntimeTargets` file changed; compiles nothing and re-archives nothing, since `sushiblas` is a static library | reconfigures and relinks | The runtime is built once in its own tree and never in a consumer's. The consumer's flags name its own stable link, so header paths and timestamps stay the same and no unit the change did not reach is compiled again |
| A public header change in SushiRuntime | nothing | the units that include it, once, and the link | reconfigures; the units that include it, and the archive | reconfigures; the units that include it, and the link | A consumer recompiles exactly what includes the header, not the library |
| A compiler change | all of it, once per configuration | all of it, once | all of it, once | its own units | The toolchain is in every key and in the tree id, so a package of another compiler is never mixed in. Nothing is shared across compilers, and nothing is built that the previous compiler's tree already holds |
| An option change in a library | nothing | its tree for the new option set, once | re-keyed through `below` | relinks | The options digest is in the tree id, so each option set has its own tree and switching back costs nothing |

A changed `*Targets.cmake` re-runs the consumer's configure step. That costs no compile. Every
library writes its generated files only when their content changes: none of the four writes a
generated header, since the version headers are hand-written and checked at configure time, and
the package files are install-tree only.

The alternatives rebuild more in each row. A per-key tree rebuilds the runtime in full for each
source change; the subdirectory design rebuilds it in every consumer; a key on the commit
rebuilds the chain for a docs commit. The table states the intent of the design for headers and
timestamps. The owner's build confirms it, and the plan lists what to look at.

## 10. Libraries and consumers

Libraries, each consumed as a package: SushiLog (`sl`), SushiProfiler (`sp`), SushiRuntime
(`sr`), SushiBLAS (`sb`). A library is also a consumer of those below it.

| Consumer | Links | Today |
| --- | --- | --- |
| SushiRuntime | SushiLog; SushiProfiler once its fragment names it | `cmake/Dependencies.cmake`: `add_subdirectory` of the SushiLog checkout |
| SushiBLAS | SushiRuntime, SushiLog | `cmake/Runtime.cmake`: `find_package(SushiRuntime QUIET)`, then `add_subdirectory`; `cmake/SushiBLASSushiLog.cmake`: `add_subdirectory` |
| SushiAI | SushiRuntime, SushiBLAS, SushiLog | `cmake/Runtime.cmake` and `cmake/BLAS.cmake`: the same two steps; `cmake/Log.cmake`: `add_subdirectory` |
| SushiDSP | SushiLog | `CMakeLists.txt` lines 30 to 36: `add_subdirectory` |
| SushiTrack | SushiLog | `cmake/SushiTrackSushiLog.cmake`: `add_subdirectory` |
| SushiEngine | SushiRuntime, SushiBLAS, SushiLog (the other session's work) | `cmake/Runtime.cmake`, `cmake/BLAS.cmake`, `cmake/BLASLibrary.cmake`, `cmake/SushiLog.cmake` |

## 11. Not done

- Packages of the consumer itself; only the libraries it depends on.
- Removal by age; only by last use and count.
- A remote store of prebuilt packages.

## 12. State of the files this design rests on

Read on 2026-10-26.

| Fact | File |
| --- | --- |
| `sr package --prefix --no-archive --force` exists and uses CPack | `sushiruntime/cli/sushiruntime/cli.py` |
| The runtime installs an export set, a config and a version file; the config loads SushiLog with `find_dependency` and recreates the SYCL target; hwloc is not in the exported interface | `sushiruntime/cmake/SushiRuntimeInstall.cmake`, `SushiRuntimeConfig.cmake.in` |
| SushiBLAS installs `SushiBLASTargets` and a config; the config loads SushiLog and SushiRuntime and includes `SushiBLASSyclHeaders.cmake`; `SushiBLASHeaderModules.cmake` is not installed | `sushiblas/modules/library/sushiblas/CMakeLists.txt` lines 84 to 112, `sushiblas/CMakeLists.txt`, `sushiblas/cmake/SushiBLASConfig.cmake.in` |
| SushiLog and SushiProfiler install an export set and a config; their CLIs (`sl`, `sp`) have no `package` command and no `cli/sushistack.deps.toml` | `sushilog/cmake/SushiLogInstall.cmake`, `sushiprofiler/cmake/SushiProfilerInstall.cmake` |
| `sushiruntime` is a `SHARED` library, `sushiblas` a `STATIC` one, SushiLog and SushiProfiler take their kind as an argument | `sushiruntime/cmake/SushiRuntimeLibrary.cmake`, `sushiblas/modules/library/sushiblas/CMakeLists.txt`, `sushilog/cmake/SushiLogLibrary.cmake`, `sushiprofiler/cmake/SushiProfilerLibrary.cmake` |
| SushiRuntime's fragment names no SushiProfiler | `sushiruntime/cli/sushistack.deps.toml` |
| SushiEngine includes `SushiBLASHeaderModules.cmake` from a SushiBLAS checkout | `sushiengine/cmake/BLAS.cmake` |
