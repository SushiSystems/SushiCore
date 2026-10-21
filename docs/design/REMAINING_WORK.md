# Remaining work

Next id: RW-55

## Decisions waiting for the owner

### RW-1 Correct `AGENTS.md` and name the skills this repository follows
- State: decision
- Done when: `AGENTS.md` names this repository's own commands and folders and the skills it
  follows

It moved from `docs/CLAUDE.md` unchanged and still tells the reader to build with `se`
(Doc D9, Lay L10, Lay L14).

### RW-2 Choose a Python-library exception to the layout, or move to it
- State: decision
- Done when: the layout rule names an exception for a Python library, or `pyproject.toml`, the
  package and `tests/` follow the rule (Lay L13, Lay L18)
- Where: `pyproject.toml`

`pyproject.toml` sits in the repository root. The layout rule forbids the file in the root. Cause:
the package was laid out as a Python library before the layout rule.

### RW-3 Keep Python 3.10 or raise the floor to 3.11
- State: decision
- Done when: `pyproject.toml` and the test matrix of `.github/workflows/ci.yml` name one floor
  (Code C18)

### RW-4 Decide what becomes of the provisioning reviews
- State: decision
- Done when: the reviews in the untracked `.superpowers/` are written into tracked reports or
  discarded, and the owner has ruled whether the provisioning, module adoption and standalone
  provisioning work get a report after the fact (Doc D10, Lay L15)

### RW-5 Choose one policy for a bad appearance value
- State: decision
- Done when: an unknown `theme`, `icons`, `color` and `background` value is handled the same way
  (Cli C7)

### RW-6 Choose how doctor groups are contributed and how `--yes` is spelled
- State: decision
- Done when: the owner has ruled whether a module contributes its groups through
  `ModuleProvision` and whether `--yes` takes `-y` here as in `hub` (Cli C16, Cli C17)

### RW-7 Decide whether the Windows GPU installer is deleted
- State: decision
- Done when: `source/sushicore/provision/gpu/windows_installer.py` is deleted, or kept with a
  caller
- Source: `docs/design/GPU_TOOLKIT_SELECTION/README.md`

No backend here calls it; hub still re-exports it.

### RW-46 Decide how a third-party licence is shown and accepted
- State: decision
- Done when: the owner has ruled how the oneAPI, winget and CUDA licences reach the user before
  setup accepts them (Lic L9, Lic L10)

## Provisioning

### RW-8 Run each module's real setup and build on the standalone layout
- State: unmeasured
- Done when: the real `setup` and build of `sr`, `sb`, `sa`, `sd`, `st` and, last, `se` have
  passed
- Source: `docs/design/STANDALONE_PROVISIONING/README.md`

Wave 4, task 17 of `docs/agent/2026_10_04_STANDALONE_PROVISIONING/PLAN.md`.

### RW-9 Run the hub root migration for real
- State: unmeasured
- Done when: the owner's `hub migrate`, each module's `doctor` and build, then
  `hub migrate --finalize` or `--rollback` have run
- Source: `docs/design/PROVISION/README.md`

Tasks 5 and 6 of `docs/agent/2026_09_25_HUB_ROOT_MIGRATION/PLAN.md`.

### RW-10 Rewrite the build caches and the local configuration to the new root
- State: open
- Done when: the migration rewrites the build caches and each module's
  `cli/config.local.toml`, so the link at the old path can go
- Source: `docs/design/PROVISION/README.md`

### RW-11 Lay toolchains out by version
- State: open
- Done when: toolchains install under `toolchains/<name>/<version>/`
- Source: `docs/design/PROVISION/README.md`

### RW-12 Build `sr` against a CUDA 13 toolkit on an Ada or newer card
- State: unmeasured
- Done when: the intel/llvm SYCL code and the Unified Runtime CUDA adapter have built against
  CUDA 13
- Source: `docs/design/GPU_TOOLKIT_SELECTION/README.md`

### RW-13 Build `sr` on the Pascal machine with the 12.9 toolkit
- State: unmeasured
- Done when: the selection gave 12.9.x in place of 12.6.3 and `sr` built
- Source: `docs/design/GPU_TOOLKIT_SELECTION/README.md`

### RW-14 Install ROCm and build `sr` on an AMD card under Linux
- State: unmeasured
- Done when: the tarball's layout past its first 60 MB, `rocm_agent_enumerator` under
  `ROCM_PATH` and the HIP adapter have run
- Source: `docs/design/GPU_TOOLKIT_SELECTION/README.md`

### RW-15 Move the build, test, package and deploy scaffold here
- State: open
- Done when: the scaffold the AI and BLAS command lines each carry in their
  `cli/.../services/project.py` lives in this package
- Source: `docs/design/PROVISION/README.md`

### RW-16 Remove `StackConfig.standalone_deps_dir`
- State: open
- Done when: `source/sushicore/stack_config.py` lacks it, one release after its last override
  is gone

### RW-17 Read a module's `fragment` key from `sushi-module.toml`
- State: open
- Done when: `setup` takes the fragment path a module declares instead of `DEFAULT_FRAGMENT`

### RW-18 Clone a Sushi library that only a fetched library pins
- State: open
- Done when: `setup` fetches a Sushi library pinned by a fetched library and by no fragment here

### RW-51 Read `use_vcpkg`
- State: open
- Done when: `stack_config.resolved_vcpkg` honours the `use_vcpkg` key the hub's defaults set per
  platform; the change reaches every command line that links this package

### RW-53 Drop the doubled progress line
- State: open
- Done when: `InstallPipeline.run` reports each step once to a human; the JSON event stays and the
  Rich bar goes

### RW-54 Provision every GPU vendor on a machine
- State: open
- Done when: `detect_gpu_vendor` returns every vendor present and the registry provisions a
  backend for each; a machine with an NVIDIA card and an AMD iGPU provisions only CUDA today

## Continuous integration

### RW-19 Add `.gitattributes` and `.editorconfig`, and finish `.gitignore`
- State: open
- Done when: the root holds both files and `.gitignore` names `.pytest_cache/` and
  `.superpowers/` (Lay L16, Lay L17)
- Where: `.gitignore`

The root has no `.gitattributes` or `.editorconfig`, and `.gitignore` has gaps. `.pytest_cache/` and
`.superpowers/` are ignored only by files their tools write inside them. Cause: the root was never
brought to the layout rule.

### RW-50 Guard the consumer contract before a tag
- State: open
- Done when: CI runs the consumer command lines' suites against the package under test, with a
  token that reads the private ones, before a release is tagged

## Command line

### RW-37 End every provisioning command with one `result` event
- State: open
- Done when: `setup`, `link` and `unlink` emit `result` through one exit helper (Cli C5)

### RW-39 Validate the workspace before `link` writes
- State: open
- Done when: `link --workspace` refuses a path without the workspace marker, and the module
  pointer and the `[modules]` entry are written as one operation (Cli C12)

### RW-41 Keep markup out of the doctor's `table` event
- State: open
- Done when: the rows of the `table` event carry plain text (Cli C2)

### RW-42 Report the file a configuration value came from
- State: open
- Done when: `config` names `config.local.toml` or the linked workspace when a value came from
  there (Cli C20)
- Where: `source/sushicore/diag.py`

`config` names `config.toml` for a value from elsewhere. A value set in `config.local.toml` or the
linked workspace shows `config.toml`. Cause: `_source_of` knows only `config.toml` and the default.

### RW-43 Say "removed" only when the build tree is gone
- State: open
- Done when: `CMakeDriver.clean_tree` checks the tree after removing it and reports a failure

### RW-52 Take a theme from a file as well as a directory
- State: open
- Done when: `LazyConsole` reads a `[cli]` theme from a file it is given, such as a workspace's
  `workspace.toml`

## Downloads

### RW-44 Pin a version and a digest for every download
- State: open
- Done when: every download in `base.deps.toml` and the fragments, `git` and `doxygen` among
  them, has a version key and a `sha256` (Code C6)
- Where: `source/sushicore/provision/manifests/base.deps.toml`,
  `source/sushicore/provision/packages/direct_download.py`,
  `source/sushicore/provision/toolchains/intel_llvm.py`

Downloads run unverified and take the newest release. Setup warns that a download is unverified.
Cause: no fragment entry pins a `sha256`, `git` and `doxygen` are declared nowhere, and `cmake`,
`ninja`, `doxygen`, `git` and `intel-llvm` are fetched as the newest release.

### RW-45 Verify shell pipelines and clones
- State: open
- Done when: the oneAPI apt key and the vcpkg, AdaptiveCpp and Unified Runtime clones are
  checked against a pinned key or commit (Code C6)
- Where: `source/sushicore/provision/system.py`, `source/sushicore/provision/gpu/adapter_builder.py`,
  `source/sushicore/provision/packages/vcpkg.py`, `source/sushicore/provision/toolchains/adaptivecpp.py`

Shell pipelines and clones are not verified. The code fetches with no digest or commit to compare.
Cause: the oneAPI apt key is piped from `curl` to `gpg`, and the vcpkg, AdaptiveCpp and Unified
Runtime clones are taken at a branch.

### RW-47 Record the failure `probe.py` swallows
- State: open
- Done when: the `except` at line 83 of `source/sushicore/provision/probe.py` logs what failed
  (Code C5)

## Code

### RW-20 Split `provision/steps.py`
- State: open
- Done when: the four step classes of `source/sushicore/provision/steps.py`, 839 lines, sit in
  files of their own (Code C1)

### RW-21 Move the setup and doctor command bodies out of `provision/commands.py`
- State: open
- Done when: `commands.py` registers commands and holds no command body

### RW-22 Declare a module's fragment path once
- State: open
- Done when: one of `StackConfig.fragment` and `ModuleProvision.fragment` holds it

### RW-23 Move the process helper below the package managers
- State: open
- Done when: `packages/base.run` sits low enough for `provision/git_client.py` to sit below
  layer 4

### RW-24 Dispatch on platform and package manager through the contracts
- State: open
- Done when: no code switches on a platform or manager name where a contract exists (Code C2)

### RW-25 Remove the consumers' names and commands from the shared code
- State: open
- Done when: the provisioning commands take the `cli/` folder and the program name from the
  module, and `InstallContext.program` has no default `hub` (Code C3, Cli C18)

### RW-26 Give the package one base error
- State: open
- Done when: failures raise one base error instead of a `bool`, `None` or a bare built-in, and
  `find_project_root` raises it in place of `SystemExit` (Code C7, Cli C8)

### RW-27 Run every child process through one brick
- State: open
- Done when: the four runner copies and the 41 direct `subprocess` calls go through one brick
  that keeps stdout to events in machine mode (Code C8, Cli C4)

### RW-28 Merge the duplicated probe tables and helpers in `provision`
- State: open
- Done when: each probe table and helper exists once (Code C9)

### RW-29 Keep Rich behind the `Renderer` seam
- State: open
- Done when: `Console.console`, `diag.py`, `discovery.py` and the call sites in `provision` reach
  Rich only through `Renderer` (Code C10, Cli C6)
- Where: `source/sushicore/diag.py`, `source/sushicore/discovery.py`

`config`, `env` and the executable picker emit no `table` or `prompt` event. Machine mode prints a
drawn table or waits on a prompt. Cause: they build Rich tables and prompts directly.

### RW-30 Replace the global console and carry the level through `Renderer.line`
- State: open
- Done when: `provision/_output.py` holds no module console and a `line` event's level comes
  from the call, not the icon (Code C11, Cli C3)

### RW-31 Shape the toolchain installers like the GPU backends
- State: open
- Done when: the toolchain installers share the GPU backends' contract (Code C12)

### RW-32 Bring docstrings to the source comment rule
- State: open
- Done when: no public symbol lacks a docstring and none exceeds eight lines; 33 and 37 on
  2026-10-19 (Code C13, Code C14, Code C21)

### RW-33 Split the units that hold more than one responsibility
- State: open
- Done when: each unit outside `steps.py` that the audit named has one responsibility (Code C15)

### RW-34 Type the untyped seams on the build side
- State: open
- Done when: the build-side seams the audit named carry types (Code C16)

### RW-35 Stop tests reaching into private names
- State: open
- Done when: no test imports or calls a name with a leading underscore (Code C19)

### RW-36 Remove hidden module state and apply the class-shape rules
- State: open
- Done when: no module keeps state outside an object, and classes outside `ui` and `help`
  follow the class-shape rules (Code C20, Code C22)

### RW-48 Break the import cycle of `workspace` and `config_base`
- State: open
- Done when: neither module imports the other, inside a function or not (Code C4)
- Where: `source/sushicore/workspace.py`, `source/sushicore/config_base.py`

`workspace` and `config_base` import each other. Lines 153 and 170 of `workspace.py`. Cause:
`workspace` imports `config_base` inside two functions to hide the cycle.

### RW-49 Remove `_first_available`
- State: open
- Done when: `source/sushicore/provision/steps.py` lacks it (Code C24)
- Where: `source/sushicore/provision/steps.py`

`_first_available` has no caller. No reference to it outside its definition. Cause: its last caller
went.

## Documentation

### RW-38 Correct the plans' paths
- State: open
- Done when: `docs/design/STANDALONE_PROVISIONING/README.md` and the two open plans cite the hub root
  migration plan and the provisioning design at their paths in this tree, and the standalone
  plan carries no absolute path and ticks its landed tasks

### RW-40 Write one reference page for the shared command surface
- State: open
- Done when: one page lists the commands, options and exit codes of every registered command,
  `config`, `env`, `--version` and `--describe` among them (Cli C11)
