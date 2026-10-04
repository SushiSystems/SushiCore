# Standalone provisioning: every module sets itself up, hub is optional

**Status:** Draft, awaiting owner review.

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
def derive(source: IDependencySource, cfg: ProvisionConfig, *,
           requested: Sequence[str] = (), gpu: bool = True) -> ToolchainSelection
```

For every `provides` group among the declared dependencies: when a member is present on the
machine, the group turns nothing on; otherwise its first declared member turns on. Declaration
order in the fragment decides the default, so the code names no toolchain. Each key in
`requested` turns its component on regardless. `gpu` turns the GPU component on when a vendor is
detected and off when the caller passes `False`.

Presence is the question `DetectStep` already answers through `probe`; `derive` asks the same
probe and does not grow a second one.

### `provision/closure.py`

Owns the fragment list for one module.

```python
@dataclass(frozen=True)
class Closure:
    sources: list[tuple[Path, str]]   # (fragment path, owner), dependencies first
    missing: list[str]                # modules named in depends_on with no checkout

def resolve(name: str, root: Path, fragment: str,
            locate: Callable[[str], Path | None]) -> Closure
```

It reads the module's fragment, follows `[module] depends_on` transitively, and asks `locate`
for each module's checkout. The base fragment comes first in `sources`. A cycle raises
`ValueError`, as `fragments.owner_order` does.

`locate` belongs to the caller. A module passes the sibling resolution it already has
(`ModuleConfig.sibling_dir`: the configured `*_dir`, the linked workspace's `[modules]`, then
the sibling directory). Hub passes its workspace lookup. The brick knows neither.

### `provision/manifests/base.deps.toml`

The shared fragment moves here from hub's package, unchanged, with a reader function beside it
that returns its path. Hub's `dependency_source` reads it from sushicore. `gui.deps.toml` is
hub's own and stays there.

### `provision/commands.py`

`ModuleProvision` gains three fields.

| Field | Type | Meaning |
| --- | --- | --- |
| `locate` | `Callable[[str], Path \| None]` | Finds a `depends_on` module's checkout. Default: finds nothing. |
| `panel` | `str \| None` | The help panel the commands are listed under. |
| `is_binary` | `Callable[[], bool]` | Reports a binary install. Default: `False`. When true, only `doctor` is registered. |

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

`StackConfig` resolves the bundled compiler and the vcpkg tree through
`provision.home.search_roots()`: `~/.sushisystems` first, then a legacy workspace tree. The
`standalone_deps_dir` hook and its two implementations go.

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
- `StackConfig.standalone_deps_dir` and `sushiruntime.config.deps_dir` are removed. Both are
  internal to the CLIs; nothing outside them calls either. The plan confirms this with a search
  before deleting.

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

## Not yet verified

- Whether `DetectStep` and `InstallDepsStep` already install cmake and ninja for a module that
  passes no base fragment. `sd setup --dry-run` on a machine without them settles it; the plan's
  first task runs it.
- How a binary engine install is told from a source checkout at the point `cli.py` registers
  commands. `ModuleProfile` carries a binary-root marker from the hub programme's wave 2; the
  plan reads it before fixing `is_binary`'s body.
