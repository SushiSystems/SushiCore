# CLI unification

**Status:** Open — shared surfaces landed in sushicore on 2026-10-05; the CLIs adopt them next.

Programme 3 of 5 in the estate refactor. Seven command line tools (`hub`, `sr`, `se`, `sa`,
`sb`, `sd`, `st`) grew the same commands separately and drifted. This programme makes the
shared part one declaration in sushicore and fixes the defects a user meets. The evidence is
the "Command line" section of each repository's `docs/agent/2026_10_05_ESTATE_AUDIT/REPORT.md`.

## Owner decisions, 2026-10-05

| # | Decision |
| --- | --- |
| D1 | The command that builds the API documentation is `docs` on every CLI |
| D2 | The container command is `container` on every CLI |
| D3 | A renamed command or flag keeps its old spelling as a hidden alias that names the new one |
| D4 | Every CLI gets `--version` and `--describe`; the `--json` event stream stays with `hub` |

`se` already has D1 to D3 with a dated alias table (`sushiengine/cli/sushiengine/aliases.py`).
Its mechanism and its date, 2027-03-25, are taken over for the other CLIs, so the hidden
spellings leave on one day everywhere. This reads D3's "one release" as that date.

## The shared surfaces

They live in sushicore and each is one call or one object.

| Surface | Brick | Replaces |
| --- | --- | --- |
| `--version`, `--describe` | `root_options.register_root_options(app, distribution=...)` | `se`'s own `--version`; `hub`'s own `--describe` |
| The catalogue `--describe` prints | `describe.catalogue(app, distribution=..., applies_to=...)` | `sushihub/describe.py` |
| `config`, `env` | `diag_commands.register_diagnostic_commands(app, diagnostics, program=..., panel=...)` | Two commands declared in six CLIs |
| Old spellings | `aliases.AliasTable(program, aliases)` and its `command(parent, word, callback, old)` | `sushiengine/aliases.py` |
| Entry point | `entry.run(app, console.error)` called from a `main()` function | Console scripts that name the Typer `app` |
| User-facing failures | `errors.SushiCoreError`, `errors.ConfigError` | Tracebacks on a malformed `config.toml` or an unknown theme |

A CLI with a root option of its own (`hub --json`) builds its callback from
`root_options.version_option` and `describe_option` instead of `register_root_options`.

## What each CLI changes

Every module CLI (`sr`, `sa`, `sb`, `sd`, `st`):

1. A `main()` that calls `sushicore.entry.run(app, console.error)`; the console script names
   it. The script line in `cli/pyproject.toml` is the orchestrator's edit.
2. `register_root_options` with the distribution name from `cli/pyproject.toml`.
3. `register_diagnostic_commands` in place of the local `config` and `env`, unless the CLI's
   `env` takes a flag of its own (`sr env --asan`), which keeps `env` local.
4. `doxygen` becomes `docs` and `docker` becomes `container`, each old word registered
   through an `AliasTable` with the date 2027-03-25.
5. The High findings of its audit section, and the Medium ones that sit inside `cli/`.
6. Tests for all of the above under `cli/tests`, the help-screen tests updated, the CLI's
   guide and README brought in line, one changelog line per scope.

Specific to one CLI:

| CLI | Change |
| --- | --- |
| `sr` | `package --prefix` refuses a filesystem root, the home directory, the project root and any ancestor of it; a non-empty directory the CLI did not stage needs `--force` |
| `sd` | Gains `clean` and `test --filter/-f`; `build -D` reaches an already configured tree |
| `st` | `-D` stops meaning `--deploy`; it stays as a hidden flag that announces `--deploy` |
| `hub` | Takes the catalogue from sushicore and adds `--version`; account and keyring failures derive from `SushiCoreError`; "not inside a workspace" is an error class, not `SystemExit(message)`; the `verify` step's broken import is fixed; under `--json` a failure still ends in one `result` event |
| `se` | Deferred: its working tree holds the owner's uncommitted work. It already has D1 to D3 and `--version`; it adopts the sushicore bricks and `--describe` afterwards |

## Not in this programme

- Renaming `hub install`, `hub doctor`, `hub link` and `hub remove` to match the module CLIs'
  `setup`, `doctor`, `link`, `unlink`. They do different work at workspace level; whether they
  share names is the owner's decision.
- Moving `build`, `test`, `run` and `clean` into sushicore. Their options differ per module for
  real reasons (`--distributed`, `--backend`, `--asan`); only the names are held equal.
- The `--json` event stream on module CLIs, and wrapping child process output into it.
- Any version number, tag or release.

## Acceptance

1. `python -m pytest` passes in sushicore and in each adopting repository's `cli/`.
2. Each adopting CLI answers `--version`, `--describe`, `config`, `env`, `docs` where it had
   `doxygen`, and `container` where it had `docker`, proven by its tests through Typer's
   test runner.
3. Each old spelling still runs, is absent from `--help` and `--describe`, and its alias row
   carries 2027-03-25.
4. A malformed `cli/config.toml` produces one line and exit code 1 through `main()`.
5. No CLI declares `config` or `env` itself, except `sr env`.
