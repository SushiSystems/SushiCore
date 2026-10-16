# Dependency fragment

A fragment is a `sushistack.deps.toml` file. It holds one table per dependency, keyed by the
dependency's name, and a reserved `[module]` table. `sushicore/deps_fragment.py` is its one
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

## The `[sushi.<name>]` pins

A module `depends_on` names is pinned in a `[sushi.<name>]` table, and each pin names a
module in `depends_on`. A module left unpinned is found through `<NAME>_DIR` and the sibling
only and is never fetched; `setup` exits 2 when neither exists, and `doctor` shows a warning
row `sushi <name>`: not pinned.

```toml
[module]
depends_on = ["sushilog"]

[sushi.sushilog]
version = "v1.0.0"                                   # the release tag
commit  = "<the 40-hex hash the tag points at>"
```

The reader raises `ValueError`, naming the file, when
a pin names a module `depends_on` does not, when `version` is empty, or when `commit` is not 40
hex digits.

`sushicore/provision/sushi_sources.py` finds a pinned library's checkout. It takes the first of
these that exists:

1. `<NAME>_DIR`, such as `SUSHILOG_DIR`: the config field `<name>_dir`, else the environment;
2. the sibling checkout `../<name>`;
3. the copy `setup` fetched, `<home>/sources/<name>/<version>/`.

`setup` first walks the pins through each resolved library's own fragment and stops when one
library is pinned at two versions, naming both pinning repositories and both versions. Then it
clones, for each pin with neither a directory nor a sibling, the tag of
`https://github.com/sushisystems/<name>.git` at depth one into the fetched folder, and removes
the folder and stops when its HEAD is not the pinned commit. A folder that already holds the
pinned commit is not cloned again. A clone that fails stops `setup` with one message naming the
library, the URL, the tag and the `<NAME>_DIR` that hands it a checkout instead.

`doctor` shows one `sushi <name>` row per pin, naming the source it found, and warns when a
sibling's HEAD is not the pinned commit. Its `sushi pins` row fails on a conflicting pin.

`StackConfig.sushi_pins(root)` reads the fragment at `StackConfig.fragment`, the path the module
also hands `ModuleProvision.fragment`. `StackConfig.sushi_definitions(root)` returns `-D<NAME>_DIR=<path>` for each pin that resolves;
the CLI adds these to the CMake configure, and CMake never downloads.

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
  on, and the run logs one warning per entry on the `sushicore.provision` logger. `doctor`
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
[Known issues](KNOWN_ISSUES.md) carries this.

When two fragments declare one entry, their `sha256` tables are joined. Where both pin the same
platform with different digests the first fragment read wins, and the merge prints a warning
naming both owners.

## Format version

A fragment carries no `format_version`. `sha256` was added on 2026-10-05 as an optional key; a
fragment without it reads as before, and a `sushicore` older than the key ignores it.
