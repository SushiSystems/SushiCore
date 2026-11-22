# sushicore/cmake

The build policy and the CMake helpers every Sushi C++ repository shares, shipped in the wheel.
`CMakeDriver.configure` puts this folder on `CMAKE_MODULE_PATH` on every configure, so a
repository writes `include(SushiBuild)` and calls what it needs. Including it defines functions
and creates nothing, so it may come before `project()`. The functions need CMake 3.29 or later.

```cmake
cmake_minimum_required(VERSION 3.29)
include(SushiBuild)
sushi_toolchain_bootstrap()
project(SushiExample LANGUAGES CXX)
sushi_build_policy()
sushi_pin_abi()
sushi_sanitizers(sushiexample)
```

## What it owns

| Function | File | Does |
| --- | --- | --- |
| `sushi_toolchain_bootstrap()`, `sushi_vcpkg_toolchain()`, `sushi_default_compiler()` | `SushiToolchain.cmake` | Before `project()`: on a Windows host, point `CMAKE_TOOLCHAIN_FILE` at the vcpkg tree `VCPKG_ROOT` names; take the `clang++` on the search path when the configure names no compiler |
| `sushi_build_policy()` | `SushiBuildPolicy.cmake` | After `project()`: link with lld on every platform through `CMAKE_LINKER_TYPE LLD`, write `compile_commands.json`, and give Debug host code `-gline-tables-only` on clang |
| `sushi_pin_abi()` | `SushiAbiPinning.cmake` | After `project()`: the release C runtime `MultiThreadedDLL` in every build type, a Debug consumer mapped to the Release build of an imported target, and `_ITERATOR_DEBUG_LEVEL=0` for the MSVC STL |
| `sushi_precompile_headers(<target> [EXTRA <header>...] [SKIP <source>...])` | `SushiPrecompiledHeaders.cmake` | Precompile the common standard headers, and the target's EXTRA ones, for every source but the SKIP ones |
| `sushi_tier_libraries(PREFIX <prefix> MACRO_PREFIX <macro> TIERS <tier>... [HEADER_FOLDER <folder>])` | `SushiTierLibraries.cmake` | Declare the tiers, lowest first, and create the shared library `<prefix>_<tier>_tier` and the export header of each |
| `sushi_tier_module(<target> <tier>)` | `SushiTierLibraries.cmake` | Make a STATIC or INTERFACE module part of its tier's library |
| `sushi_tier_link(<target> <PUBLIC\|PRIVATE\|INTERFACE> <item>...)` | `SushiTierLibraries.cmake` | Link a target with every tier module among the items resolved to its headers or its tier's library |
| `sushi_tier_archives(<target>...)` | `SushiTierLibraries.cmake` | Mark a target, such as a test or a probe, to link the archives of the tier modules it reaches, each whole on Windows, and no tier library |
| `sushi_tier_export_header(<name> <building define>)` | `SushiTierLibraries.cmake` | Write the export header of a shared library outside the tiers |
| `sushi_sanitizers(<prefix> [OPTION <name>])` | `SushiSanitizers.cmake` | Create the INTERFACE target `<prefix>_sanitizers` from the comma-separated cache entry `<PREFIX>_SANITIZE` |
| `sushi_sycl_target(<target> [DEVICE_SOURCES <source>...] [HOST_ONLY])`, `sushi_sycl_device_options(<out_compile> <out_link>)` | `SushiSyclTarget.cmake` | Apply the SYCL policy to a target: device compilation for the DEVICE_SOURCES only on intel-llvm, the whole target elsewhere |
| `sushi_check_test_sizes(<target> SOURCES <source>... [SUITE_REGEX <regex>])` | `SushiTestSizes.cmake`, `SushiCheckTestSizes.cmake` | Fail the build of a test program that declares a GoogleTest suite whose name carries no size |
| `sushi_sycl_include_dir(<out>)`, `sushi_compiler_is_sycl(<out>)`, `sushi_host_flags(<out> <flag>...)` | `SushiSyclCompiler.cmake` | Find the SYCL headers beside the compiler, and wrap a flag in `-Xarch_host` for a SYCL compiler |

`SushiBuild.cmake` includes every file but `SushiCheckTestSizes.cmake`, the script the test-size
step runs with `cmake -P`. Each file opens with `include_guard(GLOBAL)`, and each function refuses
an argument it does not know.

## Tests

`tests/test_cmake_modules/` configures the fixture projects in its `fixtures/` folder with these modules on the
module path and reads the outcome from the configure output, `build.ninja` and
`compile_commands.json`. A test skips when the machine lacks CMake 3.29, Ninja or a C++ compiler,
and on Windows when no developer environment set `LIB`.

## No option to leave the policy

The build policy, the precompiled headers and the tier libraries have no option that turns them
off. A tree that builds is a tree under the policy, so a configure never picks between two shapes
that only one of them tests. CMake 3.29 is the floor because `CMAKE_LINKER_TYPE` is read from 3.29;
`sushi_build_policy()` stops an older configure with that reason.

A precompiled header hides a missing `#include`: a unit compiles from the header's declarations
rather than its own. With no option to build without one, no build of a tree finds a missing
include in a target that takes the precompiled header.

## The tier libraries

Each tier is one shared library that holds its static modules, linked whole, and hands the
headers of all its modules to the targets that link it. A tier library links the tier below it
publicly, so a target that links one tier reaches every tier beneath. A static module compiles
with `<PREFIX>_BUILDING_<TIER>_TIER`, which makes `<MACRO>_<TIER>_API` export, and with hidden
visibility, so a symbol leaves its library only through the mark.

Every link to a module goes through `sushi_tier_link`, which resolves it when it is declared: a
module of the target's own tier is kept for its headers only, through `$<COMPILE_ONLY>`, and a
module of another tier becomes that tier's library. The code of a module therefore exists once
in the process. A module that links a module of a higher tier is refused. A module's PUBLIC and
INTERFACE links that are not tier modules are handed to the targets of its tier library too, for
their link.

No pass at the end of the configure rewrites the links, so a module comes and goes with its own
calls and touches no other target. The order it asks: a module is declared with
`sushi_tier_module` before any target links it. A link to a module not yet declared is linked as
written, and its code reaches the linking target a second time.

Both resolutions are made for the target that finally links. A target that `sushi_tier_archives`
marked (the property `SUSHI_TIER_ARCHIVES`) links every tier module it reaches as that module's
own archive and links no tier library. A program inside the tree, such as a test or a probe,
reaches internal modules the tier libraries do not export, so it links this way. On Windows the
objects of a module archive were compiled for their tier library, so a reference to another tier's
symbol is an import, and a linker binds an import to a definition in the program only once that
definition's object is loaded; an import alone loads none. There each static module links through the link
feature `SUSHI_WHOLE_ARCHIVE`, which `sushi_tier_libraries` defines: the archive stays a plain item
of the library list, so a SYCL driver sees it and links its device code and a long line still goes
to a response file, and `/WHOLEARCHIVE:<archive>` loads it whole. Elsewhere the archives link as
they are. A program the tree ships, and any unmarked target, links the tier
libraries as above.

The tier library takes no SYCL policy of its own. A tier whose modules compile device code is
given it with `sushi_sycl_target(<prefix>_<tier>_tier)`, after which its link pulls the device
images out of the archives.

## Sanitizers and SYCL

A SYCL compiler is icpx or icx, or a clang that ships the header sycl/sycl.hpp beside it, as the
intel/llvm build does. On one, `-gline-tables-only` and every sanitizer compile flag pass through
`-Xarch_host`, since the device pass rejects them or has no sanitizer runtime for every device.
On any other compiler the flags are passed as they are.

`sushi_sycl_target` reads `SushiRuntime_SYCL_TOOLCHAIN` and `add_sycl_to_target()` from the
SushiRuntime package, so that package is found first. On intel-llvm a unit compiles for the
device only when its target names it in DEVICE_SOURCES; the others compile for the host with the
SYCL headers on a system include path. The device optimisation level is `-O3` in every build
type, so a Debug test program does not run its kernels unoptimised. A static library hands its
device link options to the targets that link it, where the device link runs.
