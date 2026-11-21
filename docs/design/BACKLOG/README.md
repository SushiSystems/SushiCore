# Backlog

**Status:** Shipped — 2026-11-21
**About:** The backlog commands read the entries and mark an open entry unverified when a commit after the last green check_all run names it.
**Modules:** `source/sushicore/backlog`

## Problem

An entry is closed by a commit that names it in its `Backlog:` line, but the work in that commit
may never have passed `check_all`. `backlog list` and `backlog next` show such an entry as plainly
open, so a reader cannot tell committed work that nothing has verified from work not yet done.

Two frictions of the store itself turned up in the review of 2026-11-21. `backlog close` required
the hash of the commit that closes the entry, which does not exist until that commit does, so one
commit in eight changed nothing but the backlog and the changelog. A store holding merge conflict
markers made `backlog check` print a TOML error and one false fault for each detail file.

## Decision

The owner's ruling of 2026-11-17 (RW-59), taken as written:

- An entry is committed when a commit names it in its `Backlog:` line.
- An entry is verified when a green `check_all` run stamped a commit at or after that commit.
- `check_all` writes the stamp, the hash of `HEAD`, to `.git/sushicore/verified` after a clean run.
  A failed run writes nothing. The stamp is never committed.
- Without a stamp nothing is marked, and `list` says in one line that no verification stamp exists.
- The unverified state is derived on every read and never stored.

The owner's order of 2026-11-21 carried out four findings of the review:

- `backlog close` takes the commit as an option. Without it the changelog line names the ID alone,
  so an entry closes in the commit that does the work. A hash is optional because the changelog
  format asks for files and symbols and never for a hash.
- A store that cannot be read is one fault with its remedy. `renumber` stays the one command after
  a merge and says that it rewrote `ids.toml` and the index.
- `renumber` lives in `renumber.py`. The importer's file held five classes and two unrelated
  jobs, so a change to `renumber` was a change to the importer.
- A commit that changes nothing but `docs/backlog/` and `docs/reference/CHANGELOG.md` marks no
  entry. It files, records or closes entries and carries no work, yet the commit that filed an
  entry named it and so marked the entry it had just filed. A commit that lists no path counts as
  work.

## Design

| Piece | Job |
| --- | --- |
| `check_all.py` | After a clean run, writes `HEAD` to `<git dir>/sushicore/verified`. The git directory comes from `git rev-parse --git-dir`, so a worktree has its own stamp. Outside a git checkout it writes nothing. |
| Shell of the backlog | Reads the stamp and `git log --name-only <stamp>..HEAD`, and hands each commit's message and paths to the pure function. |
| Pure function | Takes the commits after the stamp, drops those that only change the backlog and the changelog, and returns the IDs the rest name in a `Backlog:` line; `list` and `next` mark the open entries among them unverified. |

The mark never changes an entry's state in the files.

`BacklogCheck.load` scans the files of `docs/backlog/` for conflict markers before it reads any
of them. A file that holds them is one fault, and `check_backlog` returns the faults of an unread
store without running the other rules, because each of them would report what the unread files
hide. Alternatives set aside: a git merge driver for `ids.toml`, which every clone would have to
register, and hash IDs, which would change every citation of an ID in the other repositories.
The merges of thirteen repositories show one in a hundred touching the backlog on both sides, so
neither pays for itself yet.

## Phases

| Id | Phase | State |
| --- | --- | --- |
| B1 | The stamp: check_all writes the verified commit to .git/sushicore/verified after a clean run | built |
| B2 | The mark: backlog list and next print an open entry unverified when a commit after the stamp names it | built |
| B3 | The close: backlog close takes no commit, so an entry closes in the commit that does the work | built |
| B4 | The merge: backlog check reports a conflicted or unreadable store alone, and renumber says what it rewrote | built |
| B5 | The brick: renumber.py holds renumber alone and importer.py holds the import alone | built |
| B6 | The filter: a commit that changes only the backlog and the changelog never marks an entry unverified | built |

## Open questions

- The pre-commit hook runs `check_all` before the commit exists, so the stamp it writes names the
  parent. The entries the newest commit names show as unverified although the hook just verified
  that commit. The stamp is written by `check_all.py`, a copy of the SushiSkills tool, so a stamp
  that names the verified tree and not the parent commit is a change to that repository.
