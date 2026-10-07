# sushicore.provision

The dependency root, the registry and the doctor every module CLI shares, and the four commands
that drive them: `setup`, `doctor`, `link` and `unlink`. No module needs hub installed to use
them. The designs are [`docs/design/PROVISION.md`](../../docs/design/PROVISION.md) and
[`docs/design/STANDALONE_PROVISIONING.md`](../../docs/design/STANDALONE_PROVISIONING.md).

## What it owns

| Path | Job |
| --- | --- |
| `home.py` | Resolves the dependency root, its subdirectories and the legacy trees read beside it |
| `registry.py` | Reads and writes `registry.toml`, the record of installed components and their consumers, and seeds it from a tree already on disk |
| `lock.py` | The file lock around every operation that changes the root |
| `links.py` | Makes, reads and removes a directory link: a junction on Windows, a symlink elsewhere |
| `migrate.py` | Moves a dependency root to another directory behind a journal, and rolls the move back or finalizes it |
| `user_environment.py` | Reads and writes the user's persistent environment variables: the registry on Windows, one block of `~/.profile` elsewhere |
| `fragments.py` | Merges dependency fragments from a caller-supplied source list |
| `closure.py` | Follows a fragment's `depends_on` to each module's checkout |
| `selection.py` | Decides which toolchain components a run installs |
| `manifests/` | The shared base fragment, `base.deps.toml`, and the function that returns its path |
| `integrity.py` | Compares a file's SHA-256 with an expected digest |
| `download_verifier.py` | Checks each download of a run against the digest its fragment entry pins, and names the downloads no entry pins |
| `packages/` | One file per package manager: apt, dnf, yum, pacman and zypper in `linux.py`, winget, direct download, vcpkg, GitHub releases, the GPU stack |
| `probe.py`, `system.py` | Find tools on this machine and ask the operating system |
| `toolchains/` | The intel/llvm, AdaptiveCpp and oneAPI installers, and the `.sushi_toolchain.json` stamp |
| `gpu/` | The GPU backend registry, the CUDA, ROCm and Level Zero locators, the adapter builder, the Windows installer helpers |
| `pipeline.py` | `Step`, `StepResult`, `InstallContext`, `InstallPipeline`, `ToolchainSelection` |
| `steps.py` | The shared steps: `DetectStep`, `InstallDepsStep`, `ConfigureStep`, `UninstallStep` |
| `sinks.py` | `ConfigSink` and its two forms: a workspace's `[tool]` table and a module's `cli/config.local.toml` |
| `doctor.py`, `checks.py` | The doctor framework and the stock checks |
| `config.py` | The configuration shape the steps read, and a concrete one for a standalone module |
| `_output.py` | The console the package prints through, bound by `bind_console` |
| `commands.py` | `ModuleProvision` and `register_provision_commands` |

## What it depends on

`sushicore.workspace` for the workspace file and the link pointer, `sushicore.profile` for the
module's identity, `sushicore.config_base`, `sushicore.deps_fragment`, `sushicore.build_env`,
`sushicore.errors`, and Typer inside `register_provision_commands`.

## Registering the commands

```python
import typer
from sushicore.provision.commands import ModuleProvision, register_provision_commands

app = typer.Typer()

module = ModuleProvision(
    profile=PROFILE,
    project_root=lambda: PROJECT_ROOT,
    load_config=load_config,
    console=lambda: console,
)

register_provision_commands(app, module)
```

`ModuleProvision` takes six optional fields beside the four above:

| Field | Meaning |
| --- | --- |
| `extra_checks` | Returns the module's own doctor checks. |
| `fragment` | The fragment's path below the project root; `cli/sushistack.deps.toml` by default. |
| `locate` | Finds the checkout of a module `depends_on` names. A `StackConfig` module passes `locate_sibling`. |
| `uses_base` | Adds the shared base fragment (gtest, opencl, pkgconf) before the module's own. |
| `panel` | The help panel the commands are listed under. |
| `is_binary` | Reports a binary install, which gets `doctor` alone. |

Each command binds the module's console through `bind_console` when it runs.

## The dependency root

The root is `SUSHISYSTEMS_HOME`, else `~/.sushisystems`; a consumer overrides it with
`home.bind_root(provider)`. Toolchains and vcpkg are looked up across `home.search_roots()`:
the dependency root first, then the folder `SUSHISTACK_DEPS_DIR` names and a legacy
`<workspace>/dependencies` tree. New installs go to the dependency root.
`StackConfig.dependency_roots(root)` puts the tree of the workspace a module sits in, or is
linked to, before those.

## Moving the dependency root

`migrate.plan(old_root, new_root)` reads the disk and changes nothing. It returns one `Move` per
top-level directory of the old root with its file count and bytes, the free space under the new
root, and `same_volume`. It raises `MigrationError` when the old root is missing or links
elsewhere, when one root lies inside the other, and when the new root already holds a
component's name.

`migrate.migrate(plan, report)` holds the lock at `<new root>/.lock` and takes the components
one at a time. On one volume each is renamed into the new root and journaled `moved`. Across
volumes each is copied to `<name>.partial`, compared with its source by file count and file
size, renamed into place and journaled `copied`; this path needs free space of 1.1 times the
tree. A directory link inside a component is recreated, not followed. Then the old root is
renamed to `<old>.pre-migrate` and a directory link to the new root takes its place. Loose
files at the top of the old root, its `.lock` among them, stay in the aside copy.

The journal is `<new root>/.migrate-journal.jsonl`, one JSON object per line. A run that
stopped goes on from it: finished components are not moved again and a leftover `.partial`
folder is deleted first. A rename that Windows refuses because a file is open raises
`MigrationError` naming the component; what moved before it stays journaled.

`migrate.rollback(old_root, new_root, report)` replays the journal newest first: it removes the
link, renames the aside copy back, renames each `moved` component back and deletes each
`copied` one. A copy is deleted only while the old root still holds the original. A step the
module does not know is skipped, so a caller can record its own steps with
`MigrationJournal(new_root).append(step, **fields)` and read them with `entries()`.

`migrate.finalize(old_root, new_root, report, drop_link=False)` deletes the aside copy and
renames the journal to `.migrate-journal.done.jsonl`, after which a rollback finds nothing.
With `drop_link=True` it also removes the link at the old path. It refuses when the old root is
not a link to the new root, and when there is no aside copy and the link was not asked to go.

`Registry.seed_from_tree(root, consumer)` records what a moved tree holds: each child of
`toolchains`, `tools` and `ur`, and `vcpkg`. The version is the `tag` of the component's
`.sushi_toolchain.json`, else `unversioned`.

## The user's environment

`user_environment.write_user_variable(name, value)` sets a variable for every process the user
starts from then on; `read_user_variable` and `remove_user_variable` complete the set. Each
takes a `store`, and without one uses `default_environment()`. `RegistryEnvironment` writes
`HKEY_CURRENT_USER\Environment` and broadcasts `WM_SETTINGCHANGE`. `ProfileEnvironment` keeps
`export NAME="value"` lines between two marker comments in `~/.profile` and removes the markers
with the last line. Both take what they touch as constructor arguments, the key opener and the
broadcast for one and the file for the other, so a test passes a fake key or a temporary file.

## Probing a compiler

`gpu/compiler_identity.py` reads the intel/llvm commit a SYCL compiler was built from out of
its version line, which looks like
`clang version 21.0.0git (https://github.com/intel/llvm d5f649b7...)`.

oneAPI installs system-wide, outside the dependency tree. `probe.py` therefore trusts the same
probe the active-compiler row uses, `find_sycl_compiler`, so an `icx-cl` or `icpx` that a glob
discovered counts as installed.

## Verifying downloads

A fragment entry pins the SHA-256 of the file an installer downloads for it, per platform, in
its `sha256` key. The key, and the table of which entry pins which file, are in
[`docs/reference/DEPENDENCY_FRAGMENT.md`](../../docs/reference/DEPENDENCY_FRAGMENT.md).

`integrity.verify_sha256(path, expected)` is the comparison. It raises
`sushicore.errors.DigestMismatchError`, which names the file, the expected digest and the one
found.

Three kinds of download are covered: an archive or installer fetched by
`direct_download.download`, the oneAPI installer that curl writes to a file on Windows, and the
Windows CUDA installer fetched by the GPU installer downloader. Each of those sites calls
`download_verifier.verify_download(name, path)` after the download and before it extracts or
runs the file. `name` is the fragment entry: `cmake`, `ninja`, `doxygen`, `git`, `intel-llvm`,
`adaptivecpp`, `oneapi` or `cuda`.

A download that happens inside a shell pipeline, and a git clone, are not verified. On Linux
that includes the CUDA keyring package, which `gpu/cuda.py` fetches with curl and installs with
`dpkg` as root. The full list is in
[`docs/reference/KNOWN_ISSUES.md`](../../docs/reference/KNOWN_ISSUES.md), under "Installing
third-party software".

The call
goes to the `DownloadVerifier` bound for the run. `InstallDepsStep.run` binds one built from
`IDependencySource.digests(platform)` and unbinds it when the step ends, so `hub install` and a
module's `setup` verify against the fragments they read without passing anything down. An
installer called outside that step meets a verifier that pins nothing.

The verifier is bound at module level, the way `bind_console` and `home.bind_root` are. The
download sites sit under `IPackageManager.install`, `install_gpu_stack` and the toolchain
functions, and none of those carries the run's fragments.

A file whose digest differs is deleted, and nothing between the installer and
`InstallPipeline.run` catches the error, so the install stops there. `sushicore.entry.run`
prints the message and exits 1. The installers catch `Exception` around their downloads and
re-raise this one error first.

A download whose entry pins no digest for the platform is used as before. The verifier logs one
warning per entry on the `sushicore.provision` logger and keeps the names in `unverified()`.
`doctor` has a `download digests` row from `checks.digest_check`: it warns and lists the entries
a run on this platform would download with no pin. `K_TOOL_DOWNLOADS` holds the entries Windows
fetches whatever the fragments say, and `K_DECLARED_DOWNLOADS` those fetched only when a
fragment declares them.

`gpu/windows_installer.py` also compares the Windows CUDA installer with the MD5 NVIDIA
publishes.

## The commands

### `setup`

Installs what the module needs to build and then runs `doctor`. It reads the module's fragment
and, through `[module] depends_on`, the fragment of every module it builds on, found by the
`locate` callable. `setup` never clones.

A bare `setup` installs one member of each toolchain capability a fragment marks `required`.
When something on the machine already provides `sycl-toolchain`, nothing downloads; otherwise
the first toolchain the fragment declares for it installs. The GPU toolkit installs when a
declared dependency is `gpu_only` and a card is detected.

| Option | Effect |
| --- | --- |
| `--dry-run` | Shows the run and changes nothing |
| `--yes` | Answers the LLVM download prompt |
| `--toolchain NAME` | Also installs that toolchain; may be repeated |
| `--no-gpu` | Skips the GPU toolkit |

| Exit code | When |
| --- | --- |
| 0 | Everything installed and no required check failed |
| 1 | `depends_on` forms a cycle, the lock timed out, a step failed, a download did not match its pinned SHA-256, or a required check failed |
| 2 | A module named in `depends_on` has no checkout, or `--toolchain` names an unknown toolchain |

### `doctor`

Checks the build tools, the checkouts of the modules this one builds on, the toolchain
capabilities, the fragments, the toolchain stamps and the download digests, then the module's
own checks. `--for GROUP` restricts the report to one group: `build`, `test`, `infer` or `eval`.

| Exit code | When |
| --- | --- |
| 0 | No required check failed |
| 1 | A required check failed, or `depends_on` forms a cycle |
| 2 | `--for` names an unknown group |

### `link` and `unlink`

`link` records the module in the workspace's `[modules]` table and writes a `[link] workspace`
pointer into the module's `cli/config.local.toml`; `unlink` removes both. Linking copies
nothing: config loading follows the pointer and layers the linked workspace's `[tool]` table at
read time. `SUSHISTACK_HOME` wins over the pointer, and a pointer to a deleted workspace is
ignored.

The workspace is `--workspace PATH`, else `SUSHISTACK_HOME`, else the first folder above the
project root that holds `.sushistack`.

| Exit code | When |
| --- | --- |
| 0 | The record was written or removed, or `unlink` found nothing to remove |
| 1 | The module's `cli/config.local.toml` could not be edited |
| 2 | No workspace was found |

The defects of these commands that are still open are in
[`docs/reference/KNOWN_ISSUES.md`](../../docs/reference/KNOWN_ISSUES.md).
