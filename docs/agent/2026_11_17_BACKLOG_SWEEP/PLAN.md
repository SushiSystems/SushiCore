# Backlog sweep: plan

**Status:** Open — waves A and D are committed on 2026-11-17; waves B and C wait for the next session

Closes the open work entries the owner handed over on 2026-11-17, in hierarchy order. Wave A holds
the jobs whose file sets do not meet. Wave B reshapes `provision` and the console, one seam at a
time, because its jobs share files. Wave C pins downloads and moves the machine layout. RW-50
(a CI token), RW-54 (real machines), RW-16 (a release away) and RW-15 (a move across
repositories) stay out of this plan. SushiSkills RW-61 and RW-62 run here as A2, since the shared
checkers live here. The owner approved on 2026-11-17 the breaking error change of RW-26, released
as a major version, and the toolchain layout of RW-11 with the migration of RW-10. RW-59 waits for
the owner to define "committed but unbuilt"; no design topic owns the backlog.

## Rulings

The owner handed these decisions over on 2026-11-17; each is taken on engineering grounds.

- RW-59: an entry is committed when a commit names it in its `Backlog:` line, and verified when a
  green `check_all` run stamped a commit at or after it. `check_all` writes the stamp to
  `.git/sushicore/verified`, never committed. Without a stamp nothing is marked and `list` says so
  in one line. A design topic BACKLOG records it before the code.
- KI-33: the copies that predate the move are a closed set, so their SHA-256 digests are written
  once, from SushiSkills history, to a frozen file beside the sync code; no tie to another
  repository's git at run time.
- RW-89: `Files` gains `modified_time` on disk and in memory, and `run_filtered_shards` drops its
  second port. No repository outside SushiCore implements this protocol (searched 2026-11-17).
- RW-72: `MachineActions` and `GpuStage` each get a file; `steps.py` goes.
- RW-73: `_confirm_timeout` has no caller; it and its two tests are deleted. History keeps it.
- RW-7: `windows_installer.py` has no caller but SushiStack's re-export. It is deprecated in the
  next release and deleted in the one after, with the re-export removed in SushiStack.
- RW-46: setup never accepts a third-party licence for the user. It names each licence with its
  link and waits for a yes; in machine mode it needs `--accept-licences`, and without it stops
  with exit code 2 and the list.
- RW-46, links: a shown link is the text the user accepts. winget accepts each package's own
  licence, so a winget package's link is read before the install from the `License Url` field of
  `winget show --id <id>`, VS Build Tools included; no winget link is hard-coded. A package whose
  manifest has no licence URL is shown by its id with "no licence link published". The oneAPI and
  CUDA links stay the vendors' EULA pages.
- RW-44: a download is data, not code. The fragment schema gains `version` and `url`; the names,
  repositories, assets, versions and digests of cmake, ninja, doxygen, git, intel-llvm, the LLVM
  installer and oneAPI move from the installers into `base.deps.toml`, and the installers read
  them. No installer resolves "latest"; renewing a pin is an edit of the fragment with its digest
  from the vendor's published checksum.
- RW-44, digests: where a vendor publishes no checksum file, the sha256 GitHub's release API lists
  for the asset is the digest. It comes from the release the asset is downloaded from and names
  the uploaded bytes. An asset without one, LLVM 17.0.6 and oneAPI today, stays unpinned and is
  listed in the backlog.
- RW-4: the 141 untracked review files are read, what still holds goes into a tracked report
  under `docs/agent/`, and `.superpowers/` is left for the owner to delete.

## Jobs

| Job | Files | Waits on | Status |
| --- | --- | --- | --- |
| A1 | RW-85: the shared checkers under `tools/` that walk the tree, and their tests |  | done |
| A2 | SushiSkills RW-61 and RW-62: boundary and logic tests of the shared checkers in `tools/tests/` | A1 | done |
| A3 | RW-86, RW-87, KI-33: `source/sushicore/shared_tools*` and its tests |  | done |
| A4 | RW-76: the shard runner of `source/sushicore/testing/` (not `slow_rerun.py`) and its tests |  | done |
| A5 | KI-32: the console encoding of `design show` and its test |  | done |
| A6 | RW-59: the unverified state of `source/sushicore/backlog/` and its tests |  | failed |
| A7 | RW-65: `provision/gpu/adapter_builder.py` and its callers and tests |  | done |
| A8 | RW-66: `provision/sushi_packages/clock.py`, the store, the resolver and their tests |  | done |
| A9 | RW-67, RW-71: in-memory package managers in `provision/packages/` and the tests that copy one |  | done |
| A10 | RW-20: `provision/steps.py` split into one file per step class, and its test mirror | A9 | done |
| B1 | RW-23: the process helper moved below the package managers | A10 | done |
| B2 | RW-27: one brick for every child process | B1 | done |
| B3 | RW-28: the probe tables and helpers of `provision` merged | B2 | done |
| B4 | RW-24: dispatch on platform and manager through the contracts | B3 (OS and manager chains moved; the cfg.platform chains remain) | done |
| B5 | RW-31: the toolchain installers on the GPU backends' contract | B4 | todo |
| B6 | RW-29, RW-30: Rich behind `Renderer`, no module console | B2 (ad72f9c: line level, diag and discovery; the module console and ui/help Rich imports remain) | running |
| B7 | RW-26: one base error for the package | B5, B6 | todo |
| B8 | RW-36, RW-33, RW-34: module state, split units, typed seams | B7 | todo |
| B9 | RW-35, RW-32: tests off private names, docstrings | B8 | todo |
| C1 | RW-44 (RW-105 holds the two unpinned), RW-45: a version and digest for every download, pinned keys and commits | B1 | running |
| C2 | RW-18: a Sushi library pinned only by a fetched library | A10 | done |
| C3 | RW-10, RW-11: the build caches and configuration rewritten, toolchains by version | C2 | todo |
| D1 | RW-59: design topic BACKLOG, the stamp in `check_all`, the unverified mark | A1 | done |
| D2 | KI-33: the frozen digests of the pre-move copies and their use in sync | A3 | done |
| D3 | RW-89: `modified_time` on `Files`; `filtered_run` on one port | A4 | done |
| D4 | RW-72: `machine_actions.py` and `gpu_stage.py`; `steps.py` removed | A10 | done |
| D5 | RW-73, RW-90, RW-88: the dead consent timeout, one manager order, the adaptivecpp stand-in | D4 | done |
| D6 | RW-7: deprecate the Windows GPU installer | A10 | done |
| D7 | RW-46: licence consent in setup | D4 | done |
| D8 | RW-4: the provisioning reviews into a tracked report | | done |
| E2 | RW-92: guard the portable cmake and doxygen removal | | done |

- RW-30: the provision console is carried by `ModuleProvision` and passed to each step and free
  function as a parameter; `bind_console` stays one release as a deprecated shim that sets the
  default. It runs after B5, since B4 and B5 edit the same provision signatures.
- RW-29: `ui/`, `help/`, `markup.py` and `plain_text.py` are the renderer layer itself and may
  import Rich; outside them only `renderer.py` does. `Console.console` goes once status and
  literal text have their own `Renderer` operations and events.
- RW-24, the rest: the 32 `cfg.platform == "windows"` branches switch on the run's target, so the
  target platform becomes a contract chosen once from `ProvisionConfig` (Windows and Linux plans of
  install, uninstall and detect). It runs as B4b before B5.
