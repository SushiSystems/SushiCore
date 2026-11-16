# Backlog

**Status:** Open — no phase planned yet
**About:** The backlog commands read the entries and mark an open entry unverified when a commit after the last green check_all run names it.
**Modules:** `source/sushicore/backlog`

## Problem

An entry is closed by a commit that names it in its `Backlog:` line, but the work in that commit
may never have passed `check_all`. `backlog list` and `backlog next` show such an entry as plainly
open, so a reader cannot tell committed work that nothing has verified from work not yet done.

## Decision

The owner's ruling of 2026-11-17 (RW-59), taken as written:

- An entry is committed when a commit names it in its `Backlog:` line.
- An entry is verified when a green `check_all` run stamped a commit at or after that commit.
- `check_all` writes the stamp, the hash of `HEAD`, to `.git/sushicore/verified` after a clean run.
  A failed run writes nothing. The stamp is never committed.
- Without a stamp nothing is marked, and `list` says in one line that no verification stamp exists.
- The unverified state is derived on every read and never stored.

## Design

| Piece | Job |
| --- | --- |
| `check_all.py` | After a clean run, writes `HEAD` to `<git dir>/sushicore/verified`. The git directory comes from `git rev-parse --git-dir`, so a worktree has its own stamp. Outside a git checkout it writes nothing. |
| Shell of the backlog | Reads the stamp and `git log <stamp>..HEAD`, and hands the commit messages to the pure function. |
| Pure function | Takes the commit messages after the stamp and returns the IDs they name in a `Backlog:` line; `list` and `next` mark the open entries among them unverified. |

The mark never changes an entry's state in the files.

## Phases

| Id | Phase | State |
| --- | --- | --- |
| B1 | The stamp: check_all writes the verified commit to .git/sushicore/verified after a clean run | planned |
| B2 | The mark: backlog list and next print an open entry unverified when a commit after the stamp names it | planned |

## Open questions

None.
