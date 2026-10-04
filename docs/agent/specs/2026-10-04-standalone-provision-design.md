# Standalone provisioning: every module sets itself up, hub is optional

**Status:** Design approved 2026-10-04. Plan: `../plans/2026-10-04-standalone-provision.md`.

A person who clones one open-source Sushi module must be able to build it after one command,
without installing hub. Today that holds for `sd` and `st`. `sr`, `sb` and `sa` have no `setup`
and no `doctor`, `se` has a hand-written `doctor`, and all four lean on `hub install`. This spec
gives every module CLI the same four commands from `sushicore.provision`, moves what hub still
owns alone into sushicore, and leaves hub as the place that runs the same machinery over a whole
workspace.

It builds on `2026-09-23-provision-design.md` and replaces one line of it: "`sr`, `se`, `sa` and
`sb` gain `doctor` only". Phase B of that spec, the move of hub's tree to `~/.sushisystems`,
runs after this work (`../plans/2026-09-25-hub-root-migration.md`).

## Decisions taken, 2026-10-04

| Question | Decision |
| --- | --- |
| Is hub required | No. Every module CLI provisions itself. Hub, when installed, drives the same code for every module at once. |
| What sushiengine is | The one exception. Users receive a binary through hub and a licence. The owner works from a source checkout, where `se` behaves like `sr`. |
| A module `depends_on` another | `setup` reads the fragment of every module in the chain whose checkout it can find and installs their third-party dependencies. When a checkout is missing it stops and names where to put it. It never clones. |
| What a bare `setup` installs | Enough to build. A `provides` group that something on the machine already satisfies installs nothing; otherwise its first declared member installs. More comes on request. Hub's `install` follows the same rule. |
| `se` in a binary install | `doctor` only. `setup`, `link` and `unlink` need a source tree and are absent. The fix it names is `hub install`. |
| Where shared code lives | sushicore. A module CLI keeps only what is its own: its identity, its checks, where its siblings are. |

## What is wrong today

Measured on 2026-10-04.

- PyPI carries `sushicore` 0.4.0. The working tree is at 0.6.0, and 0.5.0 and 0.6.0 were never
  tagged. `sd` and `st` require `>=0.6.0` and hub `>=0.5.0`, so none of the three installs from
  a public clone.
- `provision/commands.py` hands `setup` an empty `ToolchainSelection`. The rule that derives a
  selection from the fragments is in hub (`cli/sushihub/setup/selection.py`), with its component
  table in hub's `config.py`. A module `setup` therefore installs no SYCL toolchain.
- `setup` reads one fragment. For a module that declares `depends_on` it prints a warning and
  moves on, so `sb setup` would not install hwloc, which `sr` declares and `sb` needs.
- The shared fragment naming cmake, ninja, gtest, opencl and pkgconf ships in the hub package
  (`cli/sushihub/manifests/base.deps.toml`). A module without hub cannot read it.
- `sr` resolves its dependency tree in its own `deps_dir()`; `sb` and `sa` each carry a
  `standalone_deps_dir()` that borrows the runtime's. None of the three looks in
  `~/.sushisystems`.
- `sd` and `st` each repeat a loop that moves the four registered commands into a help panel.

## Bricks in sushicore

Each is one file with one job. Lower layers do not import higher ones.

### `provision/selection.py`

Owns which toolchain components a run installs. It holds the component table (key, label,
`ToolchainSelection` field) that hub's `config.py` holds today, and one function:

```python
def derive(source: IDependencySource, present: Mapping[str, bool], *,
           requested: Sequence[str] = (), gpu: bool = True) -> ToolchainSelection
```

For every `provides` group among the declared dependencies: when a member is present on the
machine, the group turns nothing on; otherwise its first declared member turns on. Declaration
order in the fragment decides the default, so the rule names no toolchain. Each key in
`requested` turns its component on regardless. `gpu` is passed through; the install step already
does nothing when no vendor is detected.

`present` is a plain mapping, so the rule is a pure function. The caller fills it from
`probe.toolchain_status`, the probe `DetectStep` already uses.

### `provision/closure.py`

Owns the fragment list for one module.

```python
@dataclass(frozen=True)
class Closure:
    sources: tuple[tuple[Path, str], ...]    # (fragment path, owner), dependencies first
    missing: tuple[tuple[str, str], ...]     # (module with no checkout, module that wants it)

def resolve(key: str, root: Path, locate: Locate, *, fragment: str = DEFAULT_FRAGMENT,
            shared: Sequence[tuple[Path, str]] = ()) -> Closure
```

It reads the module's fragment, follows `[module] depends_on` transitively, and asks `locate`
for each module's checkout. `shared` fragments come first in `sources`. A cycle raises
`ValueError`, as `fragments.owner_order` does.

`locate` belongs to the caller. A module passes `StackConfig.locate_sibling`: the configured
`*_dir`, then the sibling directory, which is the same place its CMake build looks. Hub passes
its workspace lookup. The brick knows neither.

### `provision/manifests/base.deps.toml`

The shared fragment moves here from hub's package, unchanged, with a reader function beside it
that returns its path. Hub's `dependency_source` reads it from sushicore. `gui.deps.toml` is
hub's own and stays there.

The install step already installs cmake, ninja, git and the host compiler whatever the
fragments say (`steps._LINUX_TOOLCHAIN_APT`, `InstallDepsStep._install_portable_tools`), which
is why `sd` and `st` work without this file. What it adds is gtest, opencl and pkgconf, which
the SYCL modules need and `sd` and `st` do not. A module therefore asks for it:
`ModuleProvision.uses_base`.

### `provision/commands.py`

`ModuleProvision` gains four fields.

| Field | Type | Meaning |
| --- | --- | --- |
| `locate` | `Callable[[str], Path \| None]` | Finds a `depends_on` module's checkout. Default: finds nothing. |
| `panel` | `str \| None` | The help panel the commands are listed under. |
| `is_binary` | `Callable[[], bool]` | Reports a binary install. Default: `False`. When true, only `doctor` is registered. |
| `uses_base` | `bool` | Whether the base fragment joins the closure. Default: `False`. |

`setup` gains `--toolchain NAME` (repeatable) and `--no-gpu`. It resolves the closure, stops
with exit code 2 and one line per missing module when `missing` is not empty, derives the
selection, and runs the pipeline it runs today. `doctor` builds its fragment check over the same
closure.

`_warn_unread_depends_on` is deleted.

### `provision/checks.py`

Two stock checks join `standard_checks`' siblings:

- `module_check(name, locate, fix)`: the checkout of a `depends_on` module exists.
- `capability_check(source, cfg, fix)`: every `provides` group has a present member.

### `stack_config.py`

`StackConfig` derives from `ProvisionSettings` and resolves the bundled compiler and the vcpkg
tree across `dependency_roots(root)`: the workspace's tree when the module sits in one, then
`provision.home.search_roots()`. It gains `locate_sibling(root, name)`. The overrides of
`standalone_deps_dir` go; the method itself stays one release, deprecated.

### `provision/probe.py`

The probe finds toolchains and vcpkg across `home.search_roots()`. Today it looks under
`home.root()` alone, so on a machine whose tree still sits in `<workspace>/dependencies` a
module `setup` would see nothing and download everything again. The 2026-09-23 spec promised
this read and the code never did it.

### `profile.py`

`ModuleProfile.key` is the lower-cased name. It is the fragment owner, the registry consumer and
the name in a workspace's `[modules]`. Today `commands.py` uses the display name, so `sd link`
writes `SushiDSP` where `hub link` writes `sushidsp`.

## Module adoption

All six CLIs end with the same registration call and no setup code of their own.

| Module | Change |
| --- | --- |
| `sr` | `Config` derives from `ProvisionSettings`; `deps_dir()` is replaced by `home.search_roots()`; registers the four commands. Its fragment does not change: `intel-llvm` is already the first `sycl-toolchain` member. |
| `sb`, `sa` | `Config` gains the provision fields through `StackConfig`; `standalone_deps_dir` is deleted; `locate` is `sibling_dir`; registers the four commands. |
| `se`, source | As `sb`. `services/doctor.py` keeps the checks that are the engine's own (the three Python extras, the validation layer, docker, the alias dates, the root marker) as `extra_checks`; cmake, ninja, ctest, doxygen, compiler, vcpkg and the runtime sibling go to the stock checks. The report becomes the shared table. |
| `se`, binary | `is_binary` reads the release marker the profile already carries. `doctor` runs the runtime checks and the licence check; each fix names `hub install`. |
| `sd`, `st` | The panel loop is replaced by `panel=`; the floor becomes `sushicore>=0.7.0`. |

Each module's README and changelog change in the same commit as its CLI.

## Hub

`cli/sushihub/setup/selection.py` and the component table in `config.py` are deleted;
`factory.build_pipeline` calls `selection.derive`. `hub install` therefore installs one SYCL
toolchain where it installed three. `--customize` stays and reads its labels from sushicore.
The catalog, `hub add`, the licence path and the binary download do not change.

`README.md`, `docs/getting_started/INSTALL.md` and `docs/design/WORKSPACE_DECOUPLING.md` say
that hub is optional and what it adds: one command over several checkouts, and the engine's
binary.

## Order

1. sushicore 0.7.0: the bricks above, with tests. The owner tags and publishes; 0.5.0 and 0.6.0
   are skipped.
2. The six module CLIs. Their file sets are disjoint, so they run as one wave.
3. Hub.
4. The dependency-root migration, whose sushicore bump becomes 0.8.0.

Until step 1 is published every CLI keeps running from its editable install on the owner's
machine, as it does now.

## Breaking changes

- `hub install` with no flags installs fewer toolchains. A machine that already has all three
  keeps them; nothing is removed.
- `se doctor` prints a table and its exit code follows the shared rule: 1 when a required check
  fails.
- `sushiruntime.config.deps_dir` is removed, and `sr` stops falling back to a repo-local
  `dependencies/` folder. `StackConfig.standalone_deps_dir` is deprecated and its overrides are
  deleted.
- `sd link` and `st link` write the lower-cased module name. `unlink` removes either spelling.

## Testing

Every brick has unit tests with fake package managers and a temporary `SUSHISYSTEMS_HOME`.
`selection.derive` is tested for a satisfied group, an unsatisfied one, a requested extra and
`gpu=False`. `closure.resolve` is tested for a chain of three, a missing middle module and a
cycle. Each module CLI gets the test `sd` has: the four commands register, `setup --dry-run`
changes nothing, and a missing `depends_on` checkout exits 2.

No task runs a build. The evidence for each module is its pytest run, `setup --dry-run` and
`doctor`. The owner runs the real `setup` and the builds.

## Out of scope

- A module CLI cloning anything, or publishing to PyPI.
- Installer scripts for the modules.
- The dependency-root migration itself.
- The 372 uncommitted files in sushiengine outside `cli/`.
- sushicore's missing documentation skeleton, still an open item from the earlier spec.

## Verified while planning

- `InstallDepsStep` installs cmake, ninja and git for a module that passes no base fragment.
  The base fragment is therefore opt-in.
- `se` has no binary command set yet. `ModuleProfile.presence(root)` tells a binary install from
  a checkout by `sushi-release.json`; `se`'s `is_binary` reads it, and returns `False` outside
  any project so `se --help` lists all four commands.
