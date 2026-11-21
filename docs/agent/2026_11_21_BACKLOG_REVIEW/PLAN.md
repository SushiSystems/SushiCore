# Backlog review: plan

**Status:** Open — J1 to J8 and J10 are done for RW-127, RW-128, RW-129 and RW-91; the removal of `backlog import` and the SushiSkills handoff follow

Applies the findings of `REPORT.md` that this repository can change, in hierarchy order: the
store's helper first, then the check that reads it, then the commands that print, then the pages.
One session carries every job out inline. The test run and the checker run come once, after the
last code job.

## Jobs

| Job | Files | Waits on | Acceptance | Status |
| --- | --- | --- | --- | --- |
| J1 | `store.py` | | `conflict_lines` numbers the marker lines of a file and no table row | done |
| J2 | `check.py` | J1 | A store with conflict markers, or an unreadable configuration, yields its own faults and no other | done |
| J3 | `editor.py`, `commands.py` | | `backlog close RW-n` prints a changelog line naming the ID alone | done |
| J4 | `commands.py`, `importer.py` tests | J1 | `backlog renumber` says it rewrote `ids.toml` and the index, and keeps the closes of both sides of a conflict | done |
| J5 | `docs/reference/BACKLOG.md`, `docs/design/BACKLOG/README.md` | J2, J3, J4 | The reference defines the four states, the post-merge steps and the close line; the topic holds phases B3 and B4 | done |
| J6 | `docs/backlog/`, `CHANGELOG.md` | J5 | RW-127 is closed in the commit that carries J1 to J5, and the changelog says so | done |
| J7 | `importer.py`, `renumber.py`, `commands.py`, tests, pages | J6 | RW-128: `renumber.py` holds renumber alone and no file in `backlog/` holds two jobs | done |
| J8 | `verification.py`, `unverified.py`, tests, the topic | J7 | RW-129: a commit that changes only the backlog never marks an entry | done |
| J9 | the SushiSkills copy of `check_backlog.py`, then `importer.py` and its tests, `command_write.py`, `check.py`, pages | J7 and SushiSkills | The removal entry: `backlog import` and the retired-files check are gone and no checker expects them | todo |
| J10 | `commands.py`, `command_context.py`, `command_read.py`, `command_write.py`, the layer table | J7 | RW-91: each command has its own registering function and none passes 60 lines | done |

## Isolation

Another session edited this checkout while the review ran, and the pre-commit hook, which checks
the working tree and not the index, refused two commits over that session's unfinished files. The
review's commits are made in a worktree of their own and reach `main` by a fast-forward.
