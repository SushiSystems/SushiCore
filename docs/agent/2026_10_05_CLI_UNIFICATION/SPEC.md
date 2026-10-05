# CLI unification

**Status:** Shipped — seven CLIs adopted the surfaces on 2026-10-05; see `REPORT.md`.

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
| D5 | `run` means "run a built executable by name" on every CLI; an application is launched by a command named after it (`se editor`, `se player`, `sd host`) |
| D6 | `build`, `test`, `run` and `clean` stay in each CLI; sushicore does not take them |
| D7 | `hub install`, `doctor`, `link` and `remove` keep their names; they are not the module CLIs' commands |
| D8 | `se` is not deferred; the owner's uncommitted files are left uncommitted |

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
| Entry point | `entry.run(app, report)` called from a `main()` function; `report` looks the console up when called, since a lazy console fails on attribute access | Console scripts that name the Typer `app` |
| User-facing failures | `errors.SushiCoreError`, `errors.ConfigError` | Tracebacks on a malformed `config.toml` or an unknown theme |

A CLI with a root option of its own (`hub --json`) builds its callback from
`root_options.version_option` and `describe_option` instead of `register_root_options`.

## What each CLI changes

Every module CLI (`sr`, `sa`, `sb`, `sd`, `st`):

1. A `main()` that calls `sushicore.entry.run(app, report)`; the console script names
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
| `sd` | `sd host` builds and launches the host GUI with `--type`, `--no-run` and arguments after `--`; `sd run [TARGET]` runs any built executable as its siblings do; `sd run` with no target keeps launching the host GUI until 2027-03-25 and announces `sd host` |
| `se` | Already has D1 to D3 and `--version`. It drops its own alias mechanism for sushicore's, gains `--describe`, takes `config` and `env` from the brick and gets the entry point. Paths the owner had modified before this work are not edited |

## Not in this programme

- Renaming `hub install`, `hub doctor`, `hub link` and `hub remove` (D7).
- Moving `build`, `test`, `run` and `clean` into sushicore (D6). Their options differ per
  module for real reasons (`--distributed`, `--backend`, `--asan`); the names and what `run`
  means are held equal.
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
