# Shared tools

**Describes:** `source/sushicore/shared_tools/commands.py`, `source/sushicore/shared_tools/sync_service.py`, `source/sushicore/shared_tools/lock_file.py`

SushiCore owns the shared checkers under its `tools/`. A repository takes them from a release tag
with `sync`, and `shared_tools.lock` in its `tools/` folder records what it took. A repository without a CLI of its
own runs the commands as `python -m sushicore.shared_tools`.

## Commands

| Command | Options | Does |
| --- | --- | --- |
| `sync ROOT` | `--tag vX.Y.Z` (required), `--from PATH`, `--force`, `--keep PATH` (repeatable), `--dry-run` | Copies the shared files of the tag into `ROOT` and writes the lock |
| `check ROOT` | none | Names each locked file that is missing or whose bytes differ from the lock |

| Code | Means |
| --- | --- |
| `0` | `sync` wrote what it should, or `check` found the repository clean |
| `1` | `sync` refused a local edit, or `check` found a file that differs or is missing |
| `2` | There is no lock, no SushiCore checkout, no such tag or no such `ROOT` |

## Where the files come from

The files are read with `git show <tag>:<path>`, never from a working tree and never at `HEAD`.
The checkout is `--from PATH`, else the sibling `../sushicore` of `ROOT`, else the copy that `setup`
keeps under `sources/sushicore/<version>/`. The shared set is every file under `tools/` and the
community files `.github/CODE_OF_CONDUCT.md` and `.github/SECURITY.md`, except `tools/settings.py`,
`tools/README.md` and `tools/known_findings.toml`, which belong to each repository.

## What a sync does

- A Python file keeps the license header the repository holds, or takes the header of its
  `tools/check_all.py` for a new file. Any other source file gets a block built from the
  repository's `tools/settings.py`. The block rules are those of the tag.
- A file whose text no release of the tools ever held is a local edit. `sync` names it and writes
  nothing unless `--force` is given.
- `--keep PATH` leaves that file as the repository holds it, and the lock omits it.
- A file the tag does not share but an earlier release did is named as dropped, never removed.
- `--dry-run` lists what would be written and writes neither the files nor the lock.

## The lock

The lock is TOML: the `tag`, the `commit` it names, and a `[files]` table from
each path to the SHA-256 of the bytes the repository holds after the sync.

```toml
tag = "v0.14.0"
commit = "0123456789abcdef0123456789abcdef01234567"

[files]
"tools/check_all.py" = "<sha256>"
```
