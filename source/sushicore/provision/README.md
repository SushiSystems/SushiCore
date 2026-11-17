# sushicore.provision

The dependency root, the registry and the doctor every module CLI shares, and the four commands
that drive them: `setup`, `doctor`, `link` and `unlink`. No module needs hub installed to use
them. The designs are [`docs/design/PROVISION/README.md`](../../docs/design/PROVISION/README.md) and
[`docs/design/STANDALONE_PROVISIONING/README.md`](../../docs/design/STANDALONE_PROVISIONING/README.md).

## What it owns

| Path | Job |
| --- | --- |
| `home.py` | Resolves the dependency root, its subdirectories and the legacy trees read beside it |
| `registry.py` | Reads and writes `registry.toml`, the record of installed components and their consumers, and seeds it from a tree already on disk |
| `lock.py` | The file lock around every operation that changes the root |
| `host/` | `IHost`, what differs by operating system (links, the root lock, registry paths, display adapters, long paths, CUDA names), with `WindowsHost`, `PosixHost` and `current_host()`, the one place that picks one |
| `target/` | `ITarget`, what the run's target platform decides (executable names, vcpkg triplet and bootstrap, adapter file names, compiler and manager choice, messages), with `WindowsTarget`, `LinuxTarget` and `target_of(cfg)`, the one place that picks one |
| `target_plans.py` | `TargetPlans`: the plans one dispatch holds, one per target, filled by the modules of the dispatch's plan package so a new target adds files and no table entry |
| `probe_plan.py`, `probe_plans/` | `IProbePlan` and `PROBE_PLANS`; `windows.py` and `linux.py` find the SYCL compiler and the local tool paths of each target |
| `manager_plan.py`, `manager_plans/` | `IManagerPlan` and `MANAGER_PLANS`; `windows.py` and `linux.py` build the package managers of each target |
| `llvm_plan.py`, `llvm_plans/` | `ILlvmPlan`, `LlvmRequest` and `LLVM_PLANS`; `windows.py` and `linux.py` supply the LLVM the acpp build needs on each target |
| `install_deps_plan.py`, `install_deps_plans/` | `IInstallPlan`, `InstallServices` and `INSTALL_PLANS`; `windows.py` and `linux.py` name the licences and run the install of each target |
| `install_location.py` | `ToolkitInstall` and `ToolkitFinder`, the `locate` contract the GPU backends and the SYCL toolchains share |
| `toolchain_install.py` | `install_toolchains` and `toolchain_licences`: walk the toolchain registry for both install plans, so a plan names no toolchain |
| `uninstall_plan.py`, `uninstall_plans/` | `IUninstallPlan`, `UninstallServices` and `UNINSTALL_PLANS`; `windows.py` and `linux.py` remove the packages and portable tools of each target |
| `links.py` | Makes, reads and removes a directory link: a junction on Windows, a symlink elsewhere |
| `migrate.py` | `migrate`, `rollback` and `finalize`: moves a dependency root to another directory behind a journal, and rolls the move back or finalizes it; re-exports the names below |
| `migration_plan.py` | `plan` and the `Move`, `MigrationPlan` and `PlanProbes` it returns and reads through: what a migration moves, worked out without changing the disk |
| `migration_movers.py` | `RenameMover` and `CopyMover`: take one component to the new root and back, by rename on one volume and by verified copy across volumes |
| `migration_journal.py` | `MigrationJournal`: the steps a migration appends to the new root, read back by a resumed run and a rollback |
| `migration_disk.py` | The path, size, copy and removal helpers a migration shares |
| `migration_error.py` | `MigrationError` |
| `user_environment.py` | Reads and writes the user's persistent environment variables: the registry on Windows, one block of `~/.profile` elsewhere |
| `user_environment_memory.py` | `InMemoryEnvironmentKey`, a registry key that holds its values in a dict |
| `fragments.py` | Merges dependency fragments from a caller-supplied source list |
| `fragments_memory.py` | `InMemoryDependencySource`, an `IDependencySource` that serves a list given in memory |
| `closure.py` | Follows a fragment's `depends_on` to each module's checkout |
| `closure_memory.py` | `TableLocator`, a module locator that answers from a table and looks at no folder |
| `selection.py` | Decides which toolchain components a run installs |
| `manifests/` | The shared base fragment, `base.deps.toml`, and the function that returns its path |
| `integrity.py` | Compares a file's SHA-256 with an expected digest |
| `download_verifier.py` | Checks each download of a run against the digest its fragment entry pins, and names the downloads no entry pins |
| `packages/` | One file per package manager: apt, dnf, yum, pacman and zypper in `linux.py`, winget, direct download, vcpkg, GitHub releases, the GPU stack; `base_memory.py` holds `InMemoryPackageManager` and its Linux form `InMemoryLinuxPackageManager`, which hold their packages in memory and run no command |
| `process_run.py` | `provision_runner(console)` and `run`: run a command, stream its output through the console they are given and return its exit code; the package managers and `git_client.py` call them |
| `probe.py`, `system.py` | Find tools on this machine and ask the operating system |
| `toolchains/` | The `Toolchain` contract and `ToolchainEnv` in `toolchain.py`, one file per toolchain (intel/llvm, AdaptiveCpp, oneAPI) each declaring its `Toolchain`, `registry.py` listing them in install order, and the `.sushi_toolchain.json` stamp. A new toolchain adds a file and one line in `registry.py`, as a GPU backend does in `gpu/registry.py` |
| `gpu/` | The GPU backend registry, the CUDA, ROCm and Level Zero locators, the CUDA and ROCm release selection, the adapter builder, the Windows installer helpers (deprecated, removed in 0.16.0); `backend_memory.py` and `windows_installer_memory.py` hold the in-memory `ToolkitLocator` and `MachineEnvironment` |
| `pipeline.py` | `Step`, `StepResult`, `InstallContext`, `InstallPipeline`, `ToolchainSelection` |
| `pipeline_memory.py` | `ScriptedStep`, a `Step` that answers a scripted result and logs that it ran |
| `machine_actions.py` | `MachineActions`: the calls the install steps make that reach the machine, each replaceable by a test |
| `gpu_stage.py` | `GpuStage` and `provision_adapters_for_run`: the compute SDK install, then the adapter builds |
| `detect_step.py` | `DetectStep`: inventories the tools and dependencies of the machine and prints the table |
| `install_deps_step.py` | `InstallDepsStep`: installs the missing manifest dependencies, the toolchains and the GPU stage |
| `configure_step.py` | `ConfigureStep`: writes the probed tool paths and the active toolchain to a `ConfigSink` |
| `uninstall_step.py` | `UninstallStep`: removes the packages, tools and config an install run placed |
| `dependency_presence.py` | Tells whether a manifest dependency is installed, by its check command or its package manager |
| `package_lists.py` | `dedup`: a list of package names without repeats, in first-seen order |
| `sinks.py` | `ConfigSink` and its two forms: a workspace's `[tool]` table and a module's `cli/config.local.toml` |
| `sinks_memory.py` | `InMemoryConfigSink`, a `ConfigSink` that records its calls and writes no file |
| `doctor.py`, `checks.py` | The doctor framework and the stock checks |
| `config.py` | The configuration shape the steps read, and a concrete one for a standalone module |
| `default_console.py` | `bind_console`, deprecated: sets the console a `ModuleProvision` without one prints through |
| `output_memory.py` | `MemoryConsole`, the in-memory console adapter a test passes to what prints |
| `sushi_sources.py` | Finds a Sushi library's checkout: `<NAME>_DIR`, the sibling, then the fetched copy |
| `pin_chain.py` | Walks the `[sushisystems.<name>]` pins of a chain and finds a library pinned at two versions |
| `git_client.py` | Clones one tag of a repository and reads a checkout's HEAD |
| `git_client_memory.py` | `InMemoryGitClient`, an `IGitClient` that clones from a table of tags and runs no git |
| `sushi_fetch.py` | `FetchSushiSourcesStep`, which clones a pinned library and checks its commit |
| `sushi_source_check.py` | The doctor rows `sushi <name>` and `sushi pins` |
| `sushi_setup.py` | The locate fallback, and the pin check, fetch and recheck `setup` runs before the closure |
| `module_checks.py` | Assembles the rows `doctor` runs for a source checkout |
| `commands.py` | `register_provision_commands`: declares the options of the four commands and ends each with one `result` event; re-exports `ModuleProvision` |
| `machine_seams.py` | `MachineSeams`: the package manager, stock check and toolchain builders a module replaces, as one value |
| `module_provision.py` | `ModuleProvision`: what one module CLI hands the shared commands, its config folder among it |
| `module_manifest.py` | The dependency fragment a module declares in its manifest, with the default when it declares none |
| `module_plan.py` | The package managers, the fragment closure and the dependency source of a module |
| `setup_command.py`, `doctor_command.py`, `link_command.py` | The bodies of `setup`, `doctor`, and `link` with `unlink`; each returns an `Outcome` |
| `outcome.py` | `Outcome`, the way a command ended, and `finish`, which sends its one `result` event |
| `sushi_packages/` | Builds each Sushi library once through its own CLI and keeps the result under `<home>/packages`: the key, the source hash, the store, the locks, the builder and the resolver. See "Sushi libraries as packages" below |
| `package_install.py`, `package_command.py` | `PackageInstaller` and `register_package_command`: the shared `package` command, which installs a built tree to a prefix and runs CPack |

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

`ModuleProvision` takes nine optional fields beside the three required ones:

| Field | Meaning |
| --- | --- |
| `console` | Returns the console every step and function of the commands prints through; the one the deprecated `bind_console` set when omitted. |
| `extra_checks` | Returns the module's own doctor checks. |
| `fragment` | The fragment's path below the project root; `cli/sushistack.deps.toml` by default. |
| `locate` | Finds the checkout of a module `depends_on` names. A `StackConfig` module passes `locate_sibling`. When `locate` returns None, `sushi_sources.resolve` looks for the module. |
| `git` | Builds the git client that fetches pinned Sushi libraries; a `GitClient` on the module's console by default. |
| `uses_base` | Adds the shared base fragment (gtest, opencl, pkgconf) before the module's own. |
| `panel` | The help panel the commands are listed under. |
| `is_binary` | Reports a binary install, which gets `doctor` alone. |
| `seams` | A `MachineSeams`: the `managers`, `base_checks` and `toolchains` builders that replace the real machine reads, passed once. |

Each command takes the console from `ModuleProvision.console` and hands it to the steps and functions it runs. `bind_console` stays one release as a deprecated shim: it sets the console a `ModuleProvision` without one uses, and warns.

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

## Sushi libraries as packages

A consumer links a Sushi library as a built package, never as a subdirectory of its own tree.
`StackConfig.sushi_packages(root, build_type, options)` returns a `PackageSet`; its `libraries`
keyword limits the resolution to the named libraries and what they depend on; the CLI uses
its `lines()`, `definitions()` and `run_dirs(platform)`. The design and its decisions are in
[`docs/agent/2026_10_26_PREBUILT_SUSHI_PACKAGES/SPEC.md`](../../docs/agent/2026_10_26_PREBUILT_SUSHI_PACKAGES/SPEC.md).

| File | Job |
| --- | --- |
| `package_request.py`, `library_node.py` | The consumer's request and one library of its chain |
| `source_locator.py`, `closure_walk.py` | Finds each library's checkout and lists the chain, dependencies first, each once |
| `source_state.py`, `configure_inputs.py`, `toolchain_identity.py`, `key_factory.py`, `package_key.py` | The key: source content, configure inputs, compiler identity, build type, options, recipe and the packages below |
| `build_tree.py`, `compiler_check.py`, `package_environment.py`, `package_builder.py` | The build in `build/pkg-<id>` through `<cli> build` and `<cli> package`, its environment and its compiler check |
| `package.py`, `package_store.py`, `package_locks.py`, `stable_link.py`, `link_publisher.py` | The store under `<home>/packages`, its three locks and the consumer's link |
| `wall_clock.py`, `monotonic_clock.py` and their `system_` and `_memory` adapters | `IWallClock`, which the store reads, and `IMonotonicClock`, which the resolver reads; `ManualWallClock` and `ManualMonotonicClock` move only when told to |
| `consumer_build.py` | What a consumer CLI takes from a `PackageSet`: `configure_arguments`, and `RunDirs`, which keeps the run-time folders in the build tree for the commands that run it |
| `forced_packages.py`, `package_choices.py`, `package_resolver.py`, `package_set.py`, `default_resolver.py` | Packages handed to a nested build, the one-key-per-library check, the resolver, its result and its assembly |

The source part of the key is the SHA-256 of the path and bytes of every tracked and every
untracked, not ignored file, without `docs/`, `build/`, `build-*/`, `*.md` and the module's
`package_exclude`. A commit that changes only documentation changes no key. The other parts are
the SYCL compiler's identity (the hash of its `--version` and its toolchain tag), the build type,
the extra `build` arguments, the recipe (`lean-1` and the SushiCore version), the configure inputs
(`cli/config.local.toml`, `vcpkg.json`, `vcpkg-configuration.json`, the vcpkg HEAD and triplet,
the CMake major and minor version) and the key digests of the packages below. So a library's key
contains its dependencies' keys, and a changed SushiRuntime gives SushiBLAS a new key.

`<home>/packages/<name>/<digest>/` holds `prefix/`, `package.stamp.json` and `.used`. The stamp is
written last; a folder without one is never used. An install goes to `<digest>.partial` and is
renamed, with retries on Windows. The store keeps the `package_keep` packages of a library chosen
most recently, and never removes one that the run chose, that a consumer's link points at, or
that a package of another library lists as built against. A removal renames the folder to
`<digest>.trash` first; one that fails is skipped with a warning and retried at the next prune. A
`.partial` folder of another process is removed only after a day.

Three locks, taken in this order and never in another: the checkout lock while a build runs in
that checkout, the key lock while a key is installed, and the consumer's link lock while its link
changes. After the key lock is taken an existing package is reused and nothing is built.

Each consumer has its own link, `<home>/packages/<name>/@<config>-<consumer>`: a directory
junction on Windows, a symlink elsewhere. It is set to the chosen package on every resolution, so
the paths in the consumer's flags do not change when a library's source changes. A nested build
reaches each package its parent hands down through a link of its own,
`@<config>-<library>-package`, so a new package below it recompiles only the files whose headers
changed, and it never moves a link of the library's own trees.

The library CLI is the only door. In the library's checkout the builder runs
`<cli> build --type <t> --build-dir build/pkg-<id> --lean <options>` and
`<cli> package --build-dir build/pkg-<id> --prefix <staging> --no-archive --force`. The
environment carries `SUSHISTACK_CXX`, one `<NAME>_PACKAGE` per package below the library and
`SUSHISTACK_PACKAGE_NESTED=1`. A CLI reads `<NAME>_PACKAGE` only beside the marker, and refuses a
package of another toolchain or build type. Before each step the compiler check probes the
`CMAKE_CXX_COMPILER` of the tree and refuses one whose identity differs from the key's.

A library with no package and no `cli` in its fragment is refused. A closure in which one library
would appear at two keys is refused naming both digests and both choosers.

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

A fragment entry pins a download with `version`, `url` and `sha256`, the three together. The
installer of a pinned entry (`cmake`, `git`) reads its address from the entry through
`download_verifier.pinned_download(name)` and resolves nothing. The keys, and the table of which
entry pins which file, are in
[`docs/reference/DEPENDENCY_FRAGMENT.md`](../../docs/reference/DEPENDENCY_FRAGMENT.md).

`integrity.verify_sha256(path, expected)` is the comparison. It raises
`sushicore.errors.DigestMismatchError`, which names the file, the expected digest and the one
found.

Two kinds of download are covered: an archive or installer fetched by
`direct_download.download`, and the oneAPI installer that curl writes to a file on Windows. Each
of those sites calls `download_verifier.verify_download(name, path)` after the download and
before it extracts or runs the file. `name` is the fragment entry: `cmake`, `ninja`, `doxygen`,
`git`, `intel-llvm`, `adaptivecpp` or `oneapi`.

The CUDA toolkit is not a fragment entry. Its release is chosen per machine, so no fragment can
pin it. `gpu/cuda_toolkit_installer.py` checks each archive against the SHA-256 that NVIDIA's
own `redistrib_<version>.json` publishes for it, before unpacking. The design is in
[`docs/design/GPU_TOOLKIT_SELECTION/README.md`](../../docs/design/GPU_TOOLKIT_SELECTION/README.md).

A download that happens inside a shell pipeline, and a git clone of third-party code, are not
verified. The clone of a pinned Sushi library is checked against its pinned commit. The full
list is in
[`docs/backlog/README.md`](../../docs/reference/KNOWN_ISSUES.md), under "Installing
third-party software".

The call
goes to the `DownloadVerifier` bound for the run. `InstallDepsStep.run` binds one built from
`IDependencySource.digests(platform)` and `downloads(platform)` and unbinds it when the step ends, so `hub install` and a
module's `setup` verify against the fragments they read without passing anything down. An
installer called outside that step meets a verifier that pins nothing.

The verifier is bound at module level, the way `home.bind_root` is. The
download sites sit under `IPackageManager.install`, `install_gpu_stack` and the toolchain
functions, and none of those carries the run's fragments.

A file whose digest differs is deleted, and nothing between the installer and
`InstallPipeline.run` catches the error, so the install stops there. `sushicore.entry.run`
prints the message and exits 1. The installers catch `Exception` around their downloads and
re-raise this one error first, and `ConfigError`, which a missing pin raises.

A download whose entry pins no digest for the platform is used as before. The verifier logs one
warning per entry on the `sushicore.provision.download_verifier` logger and keeps the names in `unverified()`.
`doctor` has a `download digests` row from `checks.digest_check`: it warns and lists the entries
a run on this platform would download with no pin. `K_DOWNLOADS` holds the
entries each platform downloads; one is listed when a fragment declares it and pins no digest.

`gpu/windows_installer.py` compares an installer with the MD5 its publisher lists. No
backend calls it since CUDA moved to the redistributable archives. It is deprecated:
it warns with `DeprecationWarning` on import and is removed in 0.16.0.

## The commands

### `setup`

Installs what the module needs to build and then runs `doctor`. It reads the module's fragment
and, through `[module] depends_on`, the fragment of every module it builds on, found by the
`locate` callable. Before that it clones each library a `[sushisystems.<name>]` pin names and no
`<NAME>_DIR` or sibling provides, and refuses a clone whose HEAD is not the pinned commit. It
never fetches an unpinned module. The pins are described in
[`DEPENDENCY_FRAGMENT.md`](../../docs/reference/DEPENDENCY_FRAGMENT.md).

A bare `setup` installs one member of each toolchain capability a fragment marks `required`.
When something on the machine already provides `sycl-toolchain`, nothing downloads; otherwise
the first toolchain the fragment declares for it installs. The GPU toolkit installs when a
declared dependency is `gpu_only` and a card is detected.

Setup never accepts a third-party licence for the user. Before anything installs, it names each
licence the run needs (winget's agreements, the Visual Studio Build Tools, Intel oneAPI, NVIDIA
CUDA) with its link and waits for a yes. A machine-mode run is never asked: without
`--accept-licences` it stops with exit code 2 and lists the licences.

| Option | Effect |
| --- | --- |
| `--dry-run` | Shows the run and changes nothing |
| `--yes` | Answers the LLVM download prompt |
| `--toolchain NAME` | Also installs that toolchain; may be repeated |
| `--no-gpu` | Skips the GPU toolkit |
| `--accept-licences` | Accepts the third-party licences setup names; a machine-mode run needs it |

| Exit code | When |
| --- | --- |
| 0 | Everything installed and no required check failed |
| 1 | The user answered no to the third-party licences, a fragment is malformed, `depends_on` forms a cycle, two pins of one library differ, a clone failed, a clone is off its pinned commit, the lock timed out, a step failed, a download did not match its pinned SHA-256, or a required check failed |
| 2 | A module named in `depends_on` has no checkout, `--toolchain` names an unknown toolchain, or a machine-mode run needs a third-party licence and `--accept-licences` was not given |

### `doctor`

Checks the build tools, the checkouts of the modules this one builds on, the toolchain
capabilities, the fragments, the toolchain stamps and the download digests, a `sushi <name>`
row per pinned library naming its source, a `sushi <name>` warning per unpinned module, and the
`sushi pins` row for conflicting pins, then the module's own checks. `--for GROUP` restricts the report to one group: `build`, `test`, `infer` or `eval`.

| Exit code | When |
| --- | --- |
| 0 | No required check failed |
| 1 | A required check failed, a fragment is malformed, or `depends_on` forms a cycle |
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
[`docs/backlog/README.md`](../../docs/reference/KNOWN_ISSUES.md).
