# Provision: one dependency root, one setup command, one doctor

**Status:** Draft, awaiting owner review.

Every Sushi Systems repository must build after one command on any machine. In SushiStack,
`hub install` does that. SushiTrack and SushiDSP are deliberately not tied to hub, so today they
have no such command: `st` has a hand-written `doctor` and no installer, `sd` has a `setup` that
reads its fragment but installs nothing into a shared place. This spec moves the machinery hub
already has into sushicore, gives it one dependency root per machine, and lets every module CLI
expose the same `setup`, `doctor`, `link` and `unlink` commands without depending on hub.

## Decisions already taken

| Question | Decision |
| --- | --- |
| Where dependencies install | `~/.sushisystems/` (`%USERPROFILE%\.sushisystems` on Windows), overridable with `SUSHISYSTEMS_HOME`. |
| Does hub use the same root | Yes. Hub stops installing into `<workspace>/dependencies/`. One tree per machine. |
| Where the code lives | A subpackage of sushicore, `sushicore.provision`. Not a separate package, not hub as a library. |
| Must hub be installed for a module to link | No. sushicore owns the reader and writer of `workspace.toml`. |
| What linking means | Record the module under `[modules]` and layer the workspace's `[tool]` selection into its config. Sharing already happens without linking. |
| Breaking hub | Only in phase B, announced to the owner first, after SushiEngine work is paused. |
| Local breakage | None allowed. Old absolute paths keep resolving through a junction until nothing uses them. |

## Sub-projects

This spec covers sub-project 1 in full and fixes the boundaries sub-projects 2 and 3 build on.
Each gets its own plan.

1. `sushicore.provision`: the moved machinery, the dependency root, the doctor framework, the
   `workspace.toml` owner and the CLI command registration.
2. Hub migration: hub consumes `sushicore.provision` and moves its tree to `~/.sushisystems/`
   (phase B below).
3. Module adoption: `st` and `sd` gain `setup`, `doctor`, `link`, `unlink`; `st` drops its own
   `proc.py`, `services/discovery.py`, the CMake driving in `services/build.py` and
   `services/tests.py`, and the vcvars snapshot in `env.py`, for the sushicore equivalents
   `sd` already uses. `sr`, `se`, `sa` and `sb` gain `doctor`.

Out of scope, recorded as backlog: the build, test, package and deploy scaffold that
`sushiai/cli/.../services/project.py` and `sushiblas/cli/.../services/project.py` each carry.

## Package layout

Lower layers never import higher ones. Each file has one job.

| Path | Job |
| --- | --- |
| `provision/home.py` | Resolves the dependency root and its subdirectories. |
| `provision/registry.py` | Reads and writes `registry.toml`, the record of installed components. |
| `provision/lock.py` | The file lock around every mutating operation. |
| `provision/fragments.py` | Merges dependency fragments from a caller-supplied source list (`IDependencySource`). |
| `provision/packages/` | `IPackageManager` and one file per manager: apt, dnf, yum, pacman, zypper, winget, direct download, vcpkg. |
| `provision/probe.py` | Finds tools on this machine: vcvars, oneAPI, cmake, ninja, doxygen, compilers. |
| `provision/toolchains/` | `intel_llvm.py`, `adaptivecpp.py`, `oneapi.py`, and `stamp.py` for `.sushi_toolchain.json`. |
| `provision/gpu/` | Backend spec and registry, CUDA, ROCm and Level Zero locators, adapter builder, Windows elevated-installer helpers. |
| `provision/pipeline.py` | `StepResult`, `Step`, `InstallContext`, `InstallPipeline`. |
| `provision/steps.py` | The shared steps: `DetectStep`, `InstallDepsStep`, `ConfigureStep`. |
| `provision/sinks.py` | `ConfigSink` and its two implementations: workspace `[tool]` and a module's `cli/config.local.toml`. |
| `provision/doctor.py` | `Check`, `CheckResult`, `Doctor`. |
| `provision/checks.py` | Stock checks every module can register. |
| `provision/commands.py` | `register_provision_commands(app, profile, extra_checks)`. |
| `workspace.py` (existing) | Gains the `[modules]` reader and writer, moved from hub's `services/links.py`. |

Two things change shape on the way in:

- `InstallContext` carries hub's SYCL options as loose fields (`oneapi`, `install_intel_llvm`,
  `install_acpp`, `gpu_vendor` and more). They become one `ToolchainSelection` value. A module
  with no SYCL options passes an empty selection.
- `ConfigureStep` writes `workspace.toml` directly. It writes to a `ConfigSink` instead, so the
  step no longer knows where its result goes. Hub passes the workspace sink, a standalone module
  passes its own.

Stays in hub: the module catalog, `hub add`/`sync`/`update`, workspace-wide fragment discovery
(hub builds the source list and hands it to `fragments.py`), the per-module readiness report,
`VerifyStep`, releases, Sushi Account, and hub's composition root in `setup/factory.py`.

## The dependency root

```
~/.sushisystems/
  registry.toml
  .lock
  toolchains/<name>/<version>/
  tools/<name>/<version>/
  vcpkg/
  ur/<vendor>-<llvm-commit>/
```

1. Directories are addressed by version. When a second module asks for a version that is
   already installed, nothing downloads. Different versions sit side by side.
2. A fragment states the requirement: a name and either a version or "any". The resolver takes
   an installed match first and installs only when none exists. The chosen path goes to the
   module's config through its sink, so pinning one module never moves another.
3. `registry.toml` records each component's name, version, path, source, install time and
   consumers. `remove` deletes a component only when no other consumer remains.
4. Install and remove hold `.lock`. The registry is written to a temporary file and renamed, so
   readers need no lock. Two terminals running `setup` at once are safe.
5. System packages from apt or winget are recorded as detected, never owned or removed.
6. Each toolchain keeps its `.sushi_toolchain.json` stamp. If the registry is lost, the stamps
   rebuild it. `doctor` reports any disagreement between the two.

## Doctor

A `Check` has a name, a group, a `required` flag and `run(ctx) -> CheckResult`. A
`CheckResult` holds a state (`ok`, `warn`, `fail`, `skip`), a detail line and `fix`, the one
command that resolves the problem.

Groups name the job a check guards: `build`, `test`, `infer`, `eval`. `<prog> doctor` runs
every group; `<prog> doctor --for infer` runs one. A failed required check sets exit code 1.
Output is the Rich table, or with `--json` the contract's `result` event.

`checks.py` supplies python, cmake, ctest, ninja, the C++ compiler (MSVC, Clang and GCC, each
reported when found), git, fragment status and toolchain stamps. A module registers its own:
SushiTrack adds the `yolox` submodule, `torch`, `torchvision`, `opencv-python` and
`pycocotools` to `infer`, and TrackEval, `numpy` and `scipy` to `eval`.

## Module commands

`register_provision_commands(app, profile, extra_checks)` adds four commands, so every module
CLI has the same ones.

| Command | Effect |
| --- | --- |
| `<prog> setup` | Detect, install the module's fragment and its `depends_on` into the root (skipping what is present), write the selection to `cli/config.local.toml`, run `doctor`. Takes `--dry-run` and `--yes`. |
| `<prog> doctor [--for GROUP]` | Read-only health report. |
| `<prog> link` | Record the module under `[modules]` in the workspace's `workspace.toml` and layer that file's `[tool]` table into the module's config. Works without hub installed. |
| `<prog> unlink` | Remove the record. Deletes nothing on disk. |

`hub doctor` and `hub install` run the same `Doctor` and pipeline over the workspace-wide
source list.

## Migration

### Phase A: nothing breaks

Covers sub-projects 1 and 3.

- `sushicore.provision` ships. Hub imports it through thin re-export modules at its old import
  paths, and its `deps_dir` still points at `<workspace>/dependencies/`.
- `home.py` reads both roots while the move is pending: a component missing from
  `~/.sushisystems/` but present in the legacy workspace tree counts as installed and is not
  downloaded again.
- `st` and `sd` gain their four commands. `sr`, `se`, `sa` and `sb` gain `doctor` only; their
  build paths do not change.

### Phase B: hub's tree moves

The owner is told before this starts and pauses SushiEngine work first.

1. Inventory: every component under `dependencies/`, and every `CMakeCache.txt`,
   `workspace.toml` and `config.local.toml` holding an old path, listed for the owner.
2. `hub migrate --dry-run` prints each move and touches nothing.
3. Each component moves on its own: a rename on the same volume, otherwise copy, verify,
   delete. Every step goes to a journal; `hub migrate --rollback` replays it in reverse.
4. The old `dependencies/` path becomes a junction (a symlink on Linux) to the new root, so
   every existing absolute path still resolves.
5. Each module's `doctor` and build run through its own CLI, and the output goes to the owner.
6. Later and separately: configs are rewritten to the new paths and build trees reconfigured.
   The junction goes only when no file names the old path, with the owner's approval.

## Testing

`provision` has unit tests with fake package managers and a temporary `SUSHISYSTEMS_HOME`: the
resolver reuses an installed version, installs a missing one, and keeps two versions apart;
`remove` keeps a component that still has a consumer; two processes contend for the lock.
Migration runs against real temporary directory trees, junction included, with a rollback test
that interrupts the move halfway.

## Open items for the owner

- sushicore has `docs/agent/` and `docs/reference/` but no `docs/design/`, `CONTRIBUTING.md`,
  `DOCUMENTATION_STYLE_GUIDE.md`, `KNOWN_ISSUES.md` or `GLOSSARY.md`. Building that skeleton is
  its own task and needs approval.
- `sushiruntime/cli/build/lib/` holds a stale copy of an old `setup/` package. It is not ours to
  delete without approval.
