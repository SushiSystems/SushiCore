# Dependency fragment

A fragment is a `sushistack.deps.toml` file. It holds one table per dependency, keyed by the
dependency's name, and two reserved tables, `[module]` and `[sushi]`; no dependency can be
named `module` or `sushi`. `sushicore/deps_fragment.py` is its one
reader; `sushicore/provision/fragments.py` merges several fragments into one list. The shared
base fragment is `sushicore/provision/manifests/base.deps.toml`.

## A dependency table

```toml
[cmake]
description   = ""        # shown by `doctor` and in the inventory
required      = true      # false: a missing one warns and does not stop the build
gpu_only      = false     # true: skipped when the GPU component is off
linux_apt     = []        # apt package names; empty means nothing to install on Linux
windows_vcpkg = []        # vcpkg port names; empty means nothing to install on Windows
check_cmd     = []        # a command; exit code 0 means the dependency is installed
provides      = ""        # a capability such as "sycl-toolchain"
sha256        = {}        # platform to the SHA-256 of the file downloaded there
```

Every key is optional. An entry with both package lists empty installs nothing through a
package manager; the toolchain entries are written that way and are fetched by their own
installers.

## The `[module]` table

| Key | Meaning |
| --- | --- |
| `depends_on` | The modules this one builds on. `setup` reads the fragment of each one it can find |
| `cli` | The command of the module's own CLI, such as `sr`. A consumer that needs a built package of this module has sushicore run `<cli> build` and `<cli> package` in its checkout |
| `package_exclude` | Git pathspecs the source hash of a package build leaves out, besides `docs/`, `*.md`, `build/` and `build-*/`. A pathspec ending in `/` is a folder prefix; any other is a glob |

## The `[sushisystems.<name>]` pins

A module `depends_on` names is pinned in a `[sushisystems.<name>]` table, and each pin names a
module in `depends_on`. A module left unpinned is found through `<NAME>_DIR` and the sibling
only and is never fetched. `setup` exits 2 when neither exists, and `doctor` shows a warning
row `sushi <name>` saying the module is not pinned.

```toml
[module]
depends_on = ["sushilog"]

[sushisystems.sushilog]
version = "v1.0.0"                                   # the release tag
commit  = "<the 40-hex hash the tag points at>"
```

A module that other modules consume as a package names its CLI in `cli`; without it a missing
package cannot be built and the consumer's `setup` stops naming the key to add. The reader raises
`ValueError` naming the file when `cli` is not a string or `package_exclude` is not a list of strings.

```toml
[module]
cli             = "sr"
package_exclude = ["bench/"]
```

The reader raises `ValueError` and names the file in four cases: a pin names a module
`depends_on` does not, `version` is empty, `commit` is not 40 hex digits, or the file holds pins
under both `[sushisystems.<name>]` and the deprecated `[sushi.<name>]`. A file with only
`[sushi.<name>]` tables reads the same pins and raises a `DeprecationWarning` naming the file.

`sushicore/provision/sushi_sources.py` finds a pinned library's checkout. It takes the first of
these that exists:

1. `<NAME>_DIR`, such as `SUSHILOG_DIR`: the config field `<name>_dir`, else the environment;
2. the sibling checkout `../<name>`;
3. the copy `setup` fetched, `<home>/sources/<name>/<version>/`.

`setup` first walks the pins through each resolved library's own fragment. When one library
is pinned at two versions it stops and names both pinning repositories and both versions.

Then it takes each pin with neither a directory nor a sibling, and clones the tag of
`https://github.com/sushisystems/<name>.git` at depth one into the fetched folder. When the
clone's HEAD is not the pinned commit, it removes the folder and stops. A folder that already holds the
pinned commit is not cloned again. A clone that fails stops `setup` with one message naming the
library, the URL, the tag and the `<NAME>_DIR` that hands it a checkout instead.

`doctor` shows one `sushi <name>` row per pin, naming the source it found, and warns when a
sibling's HEAD is not the pinned commit. Its `sushi pins` row fails on a conflicting pin.

`StackConfig.sushi_pins(root)` reads the fragment at `StackConfig.fragment`, the path the
module also hands `ModuleProvision.fragment`. `StackConfig.sushi_packages(root, build_type)` resolves a built package for every library the
chain links, and `StackConfig.sushi_definitions(root, packaged)` returns `-D<NAME>_DIR=<path>` for
each pin that resolves and is not in `packaged`. The CLI adds these and
`PackageSet.definitions()` to the CMake configure, and CMake never downloads. The packages are in
[`sushicore/provision/README.md`](../../source/sushicore/provision/README.md).

## `sha256`

`sha256` pins the file an installer downloads for the entry. It is a table with one key per
platform, `windows` or `linux`, and each value is the SHA-256 of that platform's file as 64 hex
digits in either case.

```toml
[intel-llvm]
sha256 = { windows = "<64 hex digits>", linux = "<64 hex digits>" }
```

The reader raises `ValueError`, naming the file and the entry, when `sha256` is not a table,
names another platform, or holds a value that is not 64 hex digits.

When an installer has downloaded a file it calls `verify_download` in
`sushicore/provision/download_verifier.py` before it extracts or runs it.

- The entry pins a digest for the platform and the file has it: the install goes on.
- The entry pins a digest and the file has another: the file is deleted and
  `sushicore.errors.DigestMismatchError` stops the run. Its message names the file, the pinned
  digest and the digest found.
- The entry pins nothing for the platform, or no fragment declares the entry: the install goes
  on, and the run logs one warning per entry on the `sushicore.provision.download_verifier` logger. `doctor`
  lists the same entries in its `download digests` row.

These are the downloads the verifier sees, and the entry each one is pinned under.

| Entry | Platform | File | Which version |
| --- | --- | --- | --- |
| `cmake` | `windows` | `*windows-x86_64.zip` from Kitware/CMake | The newest release on the day of the install |
| `ninja` | `windows` | `ninja-win.zip` from ninja-build/ninja | The newest release |
| `doxygen` | `windows` | `doxygen-*.windows.x64.bin.zip` from doxygen/doxygen | The newest release |
| `git` | `windows` | `*64-bit.exe` from git-for-windows/git | The newest release |
| `intel-llvm` | `windows` | `sycl_windows.tar.gz` from intel/llvm | The newest nightly |
| `intel-llvm` | `linux` | `sycl_linux.tar.gz` from intel/llvm | The newest nightly |
| `adaptivecpp` | `windows` | `LLVM-17.0.6-win64.exe` from llvm/llvm-project | Fixed in `toolchains/adaptivecpp.py` |
| `oneapi` | `windows` | `intel-oneapi-toolkit-2026.0.0.193_offline.exe` from Intel | Fixed in `toolchains/oneapi.py` |

A fragment has no key for the version of a download. Six of the eight rows resolve the newest
release, so a digest pinned for one of them stops matching on the day upstream publishes, and
the install stops there until the pin is renewed.
[Known issues](../backlog/README.md) carries this.

When two fragments declare one entry, their `sha256` tables are joined. Where both pin the same
platform with different digests the first fragment read wins, and the merge prints a warning
naming both owners.

## Format version

A fragment carries no `format_version`. `sha256` was added on 2026-10-05 as an optional key; a
fragment without it reads as before, and a `sushicore` older than the key ignores it.
`cli` and `package_exclude` are optional keys of `[module]` that a reader without them ignores.
The pin tables are `[sushisystems.<name>]` from 0.9.3, and `[sushi.<name>]` from 0.9.1 to 0.9.2.
A reader from 0.9.3 still reads `[sushi.<name>]`, with a `DeprecationWarning`. A reader older than
0.9.3 reads `[sushisystems]` as a dependency named `sushisystems`.
