# Backlog review: plan

**Status:** Open — J1 to J12 are done for RW-127, RW-128, RW-129, RW-91, RW-132 and RW-134; the SushiSkills handoff follows

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
| J9 | `importer.py`, `command_write.py`, pages | J7 | RW-133: `backlog import` is deprecated for one release, since removing it broke the siblings' shared test and SushiEngine's CLI test; its removal waits for the siblings | done |
| J10 | `commands.py`, `command_context.py`, `command_read.py`, `command_write.py`, the layer table | J7 | RW-91: each command has its own registering function and none passes 60 lines | done |
| J11 | `commit_msg.py`, `check_backlog_trailer.py`, `unverified.py`, `repo_builder.py`, their tests | J8 | RW-132: the hook accepts a sibling's entry and the amend of a closing commit, and a test that runs inside a commit is not mistaken for an amend | done |

| J12 | `pre_commit.py`, `pre-commit`, `test_pre_commit.py` | J11 | RW-134: the pre-commit hook checks the files the commit will hold, from a copy of the index | done |

## Isolation

Another session edited this checkout while the review ran, and the pre-commit hook, which checked
the working tree and not the index, refused four commits over that session's unfinished files. The
review's commits were made in a worktree of their own and reached `main` by a fast-forward; since
RW-134 the hook checks the index, so a shared checkout no longer needs the worktree for this.
