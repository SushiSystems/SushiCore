# CLI unification report

**Status:** Seven CLIs done and committed locally on 2026-10-05. Nothing is pushed.

## What was done

| Step | Repository | Commit | Tests run by the orchestrator |
| --- | --- | --- | --- |
| Shared surfaces | sushicore | `c6e3f08`, `3fe85f0` | 830 passed |
| `hub` | sushistack | `be111fc` | 316 passed |
| `sr` | sushiruntime | `7274fd5` | 132 passed |
| `sa` | sushiai | `ac96b89` | 78 passed, two files left out (see below) |
| `sb` | sushiblas | `532ce85` | 55 passed |
| `sd` | sushidsp | `0c64c29` | 87 passed |
| `st` | sushitrack | `a45be00` | 113 passed |
| `se` | sushiengine | `46eb0b9f` | 936 passed, 12 failed before and after (see below) |

Each CLI was changed by one agent, reviewed by a second against the spec, and corrected by a
third where the review found a Critical or Important defect. The review of `sr` found that the
tests guarding the `package --prefix` refusals could not fail; they were rewritten and each was
seen failing with its rule removed.

## What a user meets

- Every CLI answers `--version` and `--describe`.
- A malformed `cli/config.toml` or an unknown theme ends in one line and exit code 1.
- `doxygen` is `docs` on `sr`, `sa`, `sb`, `sd`; `docker` is `container` on `sr`, `st`. The old
  words run, hidden, and name the new one on a terminal until 2027-03-25.
- `sd host` launches the host GUI; `sd run TARGET` runs a built executable. `sd run` with no
  target, `sd run --type X` and `sd run -- ARGS` still launch the host GUI until 2027-03-25.
- `sr package --prefix` refuses a filesystem root, the home directory, the project root and its
  ancestors, and needs `--force` for a non-empty directory it did not stage.
- `st build -D` no longer means `--deploy`; it is a hidden flag that announces `--deploy`.
- `hub` account, keyring and network failures are one error line; under `--json` a failure
  ends in one `result` event. The `verify` and `all` setup steps are gone: `verify` imported a
  module that no longer exists.

## Behaviour changes the agents made beyond the spec

- `sr`: the project root is the directory holding `sushi-module.toml`, not the nearest
  `CMakeLists.txt`. A checkout without that file is no longer recognised.
- `sd`: `sd host` always builds before launching; Ctrl+C exits 130; `sd test` runs ctest from
  `build/` through sushicore's driver; `llvm_root` left the overridable fields.
- `st`: `st eval` with no matching sequence exits 1; `st clean` exits 1 when a directory survives.
- `sa`: `--help` on `train`, `inference` and `demo mlp` exits 1 when the program is not built.
- `se`: `se env` gained `-a`; `sushiengine.aliases` no longer exports `alias_for`, `announce`,
  `deprecated` and `expired`; callers use `aliases.TABLE`.
- `hub`: an unreachable server raises `AccountUnreachable` where it raised `LoginError`.

## Rulings

- The hidden spellings leave on 2027-03-25, the date `se` already used, not "after one
  release". Cost if wrong: one date in six alias tables.
- The spec was written and executed without a separate review by the owner, who answered the
  four interface questions it rests on and four more during the work.
- `sd run -- ARGS` was added to the old spellings by the orchestrator after the agents left it
  out: the old help text taught exactly that form.
- In sushiengine only the paths the owner had not modified were committed. Six changelog
  lines for the `se` change sit in `docs/reference/CHANGELOG.md` beside the owner's
  uncommitted entries and were left for the owner to commit.
- `entry.run` takes a reporter that is looked up when called. The first wording,
  `entry.run(app, console.error)`, fails on a CLI whose console builds on attribute access;
  the docstring, README and spec were corrected.

## For the owner

Decisions the spec does not make and the agents left alone:

1. One flag for the interactive pick: `--pick` (`se`), `--sort` (`sr`, `sa`, `sb`, `sd`),
   `--select` (`st`).
2. Whether `run` builds first: `se run` does unless `--no-build`; `sb` and `sd` do not.
3. `sd`: what a bare `sd run` does after 2027-03-25, and the fate of `target_bin`.
4. `--describe` lists hidden options, such as the old `--type` on `sd run`.
5. `hub --json`: a usage error and a bare `hub --json` produce no `result` event;
   `status --json` duplicates the root flag; `hub --json --version` prints plain text.
6. Help panel names differ per CLI (Project, Build, Application, Diagnostics, Environment).
7. Version numbers: sushitrack states 0.1.0, 2.0.0 and a third in CMake; the `sr` CLI says
   1.0.0 while the product is 0.3.0; sushicore is still 0.7.0 with new public API.
8. `sr test --distributed` does nothing; `--asan` is spelt three ways on `sr`.
9. `st setup --help` shows SYCL options SushiTrack does not use; they come from sushicore.
10. sushicore still raises `SystemExit(message)` for a command run outside a checkout, and
    `CMakeDriver.clean_tree` prints "removed" whether or not the tree is gone.
11. Dead code the audit named in `hub` was not deleted: deleting it is the owner's call.

## What was not done

- The installed commands on this machine still call the old entry point until each CLI is
  reinstalled; until then a malformed config is still a traceback there. `st` is unaffected.
- No CLI was run as a process and nothing was built. Every proof is a test through Typer's
  runner or a recorded argv.
- `sushiai`: `tests/test_demo.py` and `tests/test_train.py` run built binaries and fail on this
  machine with a missing SYCL kernel; they failed before this work and were left out.
- `sushiengine`: 12 tests fail before and after: seven need the network, three packaging
  tests, and two that depend on the owner's recent or uncommitted work.
- The `--json` event stream on module CLIs; services that print and return codes; a shared
  build registrar. All are outside the spec.
