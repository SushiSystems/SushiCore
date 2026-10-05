# sushicore.provision

The dependency root, the registry and the doctor every module CLI shares, and the four commands
that drive them: `setup`, `doctor`, `link` and `unlink`. No module needs hub installed to use
them. The designs are [`docs/design/PROVISION.md`](../../docs/design/PROVISION.md) and
[`docs/design/STANDALONE_PROVISIONING.md`](../../docs/design/STANDALONE_PROVISIONING.md).

## What it owns

| Path | Job |
| --- | --- |
| `home.py` | Resolves the dependency root, its subdirectories and the legacy trees read beside it |
| `registry.py` | Reads and writes `registry.toml`, the record of installed components and their consumers |
| `lock.py` | The file lock around every operation that changes the root |
| `fragments.py` | Merges dependency fragments from a caller-supplied source list |
| `closure.py` | Follows a fragment's `depends_on` to each module's checkout |
| `selection.py` | Decides which toolchain components a run installs |
| `manifests/` | The shared base fragment, `base.deps.toml`, and the function that returns its path |
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
| 1 | `depends_on` forms a cycle, the lock timed out, a step failed, or a required check failed |
| 2 | A module named in `depends_on` has no checkout, or `--toolchain` names an unknown toolchain |

### `doctor`

Checks the build tools, the checkouts of the modules this one builds on, the toolchain
capabilities, the fragments and the toolchain stamps, then the module's own checks. `--for GROUP`
restricts the report to one group: `build`, `test`, `infer` or `eval`.

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
