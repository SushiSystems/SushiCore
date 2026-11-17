# Dependency fragment

A fragment is a `sushistack.deps.toml` file. It holds one table per dependency, keyed by the
dependency's name, and two reserved tables, `[module]` and `[sushisystems]`; no dependency can be
named `module` or `sushisystems`. The old name `[sushi]` is read as `[sushisystems]` with a deprecation warning. `sushicore/deps_fragment.py` is its one
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
ref           = ""        # the tag or branch a clone's commit was resolved from
commit        = ""        # the 40-hex commit a clone must end at
fingerprint   = ""        # the 40-hex fingerprint of a signing key
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
module also hands `ModuleProvision.fragment`. A module names its fragment in `[module] fragment` of `sushi-module.toml`;
without it the path is `cli/sushistack.deps.toml`. `StackConfig.sushi_packages(root, build_type)` resolves a built package for every library the
chain links, and `StackConfig.sushi_definitions(root, packaged)` returns `-D<NAME>_DIR=<path>` for
each pin that resolves and is not in `packaged`. The CLI adds these and
`PackageSet.definitions()` to the CMake configure, and CMake never downloads. The packages are in
[`sushicore/provision/README.md`](../../source/sushicore/provision/README.md).

## `version`, `url` and `sha256`

An entry that pins a download carries three keys together. `version` is the release the file
belongs to, as the vendor names it. `url` is a table with one key per platform, `windows` or
`linux`, holding the exact `https` address of that platform's file. `sha256` is a table with the
same keys, each value the SHA-256 of that file as 64 hex digits in either case, taken from the
vendor's own published checksum.

```toml
[cmake]
version = "v4.5.0"
url     = { windows = "https://github.com/Kitware/CMake/releases/download/v4.5.0/cmake-4.5.0-windows-x86_64.zip" }
sha256  = { windows = "<64 hex digits>" }
```

The reader raises `ValueError`, naming the file and the entry, when an entry declares one or two
of the three keys, when `url` and `sha256` name different platforms, when a key is not the shape
above, or when a digest is not 64 hex digits. An entry that declares none of the three pins
nothing.

When an installer has downloaded a file it calls `verify_download` in
`sushicore/provision/download_verifier.py` before it extracts or runs it.

- The entry pins a digest for the platform and the file has it: the install goes on.
- The entry pins a digest and the file has another: the file is deleted and
  `sushicore.errors.DigestMismatchError` stops the run. Its message names the file, the pinned
  digest and the digest found.
- The entry pins nothing for the platform, or no fragment declares the entry: the install goes
  on, and the run logs one warning per entry on the `sushicore.provision.download_verifier` logger. `doctor`
  lists the same entries in its `download digests` row.

An installer of a pinned entry takes its address from `pinned_download(name)`; when no fragment
pins the entry it stops with `sushicore.errors.ConfigError` naming it.

These are the downloads the verifier sees. Every one but the last two is pinned in the base
fragment. The digest of `cmake` and `git` is the vendor's checksum file or release notes; for
`ninja`, `doxygen` and `intel-llvm`, whose projects publish none, it is the `digest` GitHub's
release API lists for the asset, which names the uploaded bytes.

| Entry | Platform | File | Version | Pinned |
| --- | --- | --- | --- | --- |
| `cmake` | `windows` | `cmake-4.5.0-windows-x86_64.zip` from Kitware/CMake | `v4.5.0` | Yes, from Kitware's `cmake-4.5.0-SHA-256.txt` |
| `git` | `windows` | `Git-2.56.1-64-bit.exe` from git-for-windows/git | `v2.56.1.windows.1` | Yes, from the release notes' hash table |
| `ninja` | `windows` | `ninja-win.zip` from ninja-build/ninja | `v1.13.2` | Yes, from the GitHub release API |
| `doxygen` | `windows` | `doxygen-1.18.0.windows.x64.bin.zip` from doxygen/doxygen | `Release_1_18_0` | Yes, from the GitHub release API |
| `intel-llvm` | `windows` | `sycl_windows.tar.gz` from intel/llvm | `nightly-2026-11-17` | Yes, from the GitHub release API |
| `intel-llvm` | `linux` | `sycl_linux.tar.gz` from intel/llvm | `nightly-2026-11-17` | Yes, from the GitHub release API |
| `adaptivecpp` | `windows` | `LLVM-17.0.6-win64.exe` from llvm/llvm-project | Fixed in `toolchains/adaptivecpp.py` | No: the release lists no digest |
| `oneapi` | `windows` | `intel-oneapi-toolkit-2026.0.0.193_offline.exe` from Intel | Fixed in `toolchains/oneapi.py` | No: no checksum found on Intel's download page |

Renewing a pin is an edit of the entry: the new version, the new address and the digest from the
same source as before.

When two fragments declare one entry, their `url` and `sha256` tables are joined. Where both
pin the same platform differently, or name different versions, the first fragment read wins, and
the merge prints a warning naming both owners.

## `ref`, `commit` and `fingerprint`

An entry that pins a git clone carries `ref` and `commit` together. `commit` is the full 40-hex
hash the clone must end at, in either case. `ref` is the tag or branch the hash was resolved from
with `git ls-remote`; it is a record and is never fetched. The installer fetches the hash alone,
and when `git rev-parse HEAD` is another commit it stops with
`sushicore.errors.CommitMismatchError`, which names both commits.

```toml
[adaptivecpp]
ref    = "v24.10.0"
commit = "7677cf6eefd8ab46d66168cd07ab042109448124"
```

An entry that pins a signing key carries `fingerprint`, the 40 hex digits of the primary key,
with or without spaces. The installer downloads the key to a file, reads its primary-key
fingerprints with `gpg --show-keys --with-colons`, and installs the key only when one of them is
the pin; otherwise it reports one error and installs nothing. A subkey does not count.

The reader raises `ValueError`, naming the file and the entry, when `commit` or `fingerprint` is
not 40 hex digits, or when only one of `ref` and `commit` is declared. When two fragments declare
one entry with different values of these keys, the first read wins and the merge prints a warning.

The base fragment pins these entries:

| Entry | Pins | Read by |
| --- | --- | --- |
| `vcpkg` | `master` at its commit | `packages/vcpkg.py` |
| `adaptivecpp` | `v24.10.0` at its commit | `toolchains/adaptivecpp.py` |
| `unified-runtime` | the intel/llvm commit of the pinned nightly | `gpu/adapter_builder.py` |
| `oneapi-apt-key` | the fingerprint of the Intel apt signing key | `intel_oneapi_repo.py` |

Renewing one is an edit of the entry: `git ls-remote` for the new hash, or the new key's
fingerprint from Intel.

## Format version

A fragment carries no `format_version`. `sha256` was added on 2026-10-05 as an optional key; a
fragment without it reads as before, and a `sushicore` older than the key ignores it. `version`
and `url` were added with it as a rule: an entry with a `sha256` and no `version` or `url` is now
refused, where it was read before.
`cli` and `package_exclude` are optional keys of `[module]` that a reader without them ignores.
The pin tables are `[sushisystems.<name>]` from 0.9.3, and `[sushi.<name>]` from 0.9.1 to 0.9.2.
A reader from 0.9.3 still reads `[sushi.<name>]`, with a `DeprecationWarning`. A reader older than
0.9.3 reads `[sushisystems]` as a dependency named `sushisystems`.
