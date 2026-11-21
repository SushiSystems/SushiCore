# Backlog review: report

The owner asked whether the backlog system is good for people and for agents, and where it slows
work or pulls an agent off the rules. This report holds what was measured, what the literature
says and what each finding became. Every number was read from this repository, from the thirteen
repositories of the workspace that hold a backlog, or from a run in a throwaway clone. Nothing in
the report comes from memory.

## Method

| Source | Read |
| --- | --- |
| `git log 56ddb6f..HEAD` | The 228 commits since `K_TRAILER_SINCE`: trailers, files touched, closed IDs, dates |
| Throwaway clone of the repository | Five merges of two backlog edits, and one real commit through the hooks |
| `git log --merges` of 13 repositories | Merges whose two sides both changed `docs/backlog/` |
| `wc` over the files a session loads | The size of the rules an agent reads before it starts |
| `python -m sushicore.backlog` | The time of `next`, `check` and `list`; the age of every open entry |
| Web search, 11 queries | Prior art and studies, listed under "Literature" |

The commit statistics cover 22 days, from 2026-10-30 to 2026-11-21. The scripts ran from the
scratchpad and read the repositories without writing to them.

## Measurements

### Commits that change nothing but the backlog

228 commits, 123 naming an ID, 105 with `Backlog: none`, none without a line. Of them, 38 touch
only `docs/backlog/` and the changelog: 27 close entries, 10 file or record them, 1 other. The
share did not move across the RW-59 commit: 27 of 166 before it, 11 of 60 after.

| Cost | Measured |
| --- | --- |
| Pre-commit hook (`check_all`, 23 checkers and the tests) | 32 s |
| A commit through both hooks | 35 s |
| The commit-msg hook alone | 0.42 s |
| `backlog next`, `check`, `list` | 0.31 s, 0.26 s, 0.30 s |

The 27 closing commits cost about 16 minutes of hook time and one line of history each. Closing
needed a commit hash, which the closing commit cannot know, and `close --commit` was required.
The changelog format asks for files and symbols and names no hash, yet 20 of its 30 entries carry
one.

### What `Backlog: none` is used for

The hook accepts any non-empty reason. The 103 non-merge commits that use it sort as follows.

| Reason given | Commits |
| --- | --- |
| Work of a plan or a review whose jobs are not backlog entries | 34 |
| A release | 21 |
| Closing, filing or recording an entry | 18 |
| An entry of another repository, which the trailer cannot cite | 9 |
| A correction of the previous commit, or a defect fixed the same day | 8 |
| The owner's ruling | 5 |
| A copy of the shared tools, or a setting | 4 |
| Other | 4 |

Three commits say outright that no entry exists. The other 100 name a reason the grammar has no
word for. The rate of 46 percent measures the gap between the grammar and the way work is
organised: plans and the backlog are two lists. The reasons show no sign of evasion.

### Two branches that edit the backlog

| Branch A | Branch B | Git |
| --- | --- | --- |
| adds, area X | adds, area Y | conflict in `README.md` only; both took the same ID |
| adds, area X | adds, area X | conflict in the area file |
| closes RW-91 | closes RW-95 | conflict in `ids.toml` |
| adds | closes | conflict in `README.md` and `ids.toml` |
| sets a column | sets a column elsewhere | clean |

`backlog renumber` resolved the conflicted `ids.toml` (union of the closed numbers, highest
counter), rewrote the index and renamed the shared ID; `check` was clean afterwards. Its output
said "no ID is shared" and nothing about the files it had rewritten. Before `renumber`, `check` on
a conflicted `ids.toml` printed a TOML parse error and one false "is closed" fault for every
detail file, because every rule ran on files it had not read.

Across 13 repositories there are 102 merges in 11,650 commits, and one merge, in SushiDSP, had the
backlog changed on both sides.

### The verification mark

In a clone with the hooks installed, a commit that only filed an entry went through the hook in
35 s. The stamp afterwards named the parent of the new commit, and `list` printed the entry it had
just filed as `unverified` at age 0d. The hook verifies the tree of the commit it guards and
writes the hash of the commit before it, so the newest commit's entries are always marked.

### Sizes and ages

| Measured | Value |
| --- | --- |
| Rules a session loads: `CLAUDE.md` chain, 13 skills, four format pages | 75.7 KB, about 19,000 tokens at four bytes each |
| Of which the backlog's: the skill, `BACKLOG_FORMAT.md` and its block | about 9 KB |
| Work entries open now | 42: 6 at P1 (one a decision), 16 at P2, 20 at P3; 1 late |
| Lifetime of closed P1 entries | 7 closed, median 0 days, longest 1; limit 14 |
| Lifetime of closed P2 entries | 65 closed, median 11 days, longest 29; limit 90 |
| Lifetime of closed P3 entries | 10 closed, median 3.5 days, longest 18; limit 180 |
| The line "Take what it gives" | 12 repository `CLAUDE.md` files, the skill and the template |
| Repositories holding the retired files `backlog import` reads | 0 of 21 |

No closed entry has passed its limit. The oldest open entry was opened on 2026-10-19, so the P2
and P3 limits have no data to be judged against yet.

## Corrections to the first assessment

| First claim | Finding |
| --- | --- |
| `renumber` does nothing on a conflicted `ids.toml` | It merges both sides. Only its message was wrong, and `check` before it was cryptic |
| `none` at 46 percent is the cheapest way round the rules | 100 of 103 reasons are cases the grammar cannot express; three admit no entry |
| Closing in a later commit is the RW-59 workflow | The share of closing commits is the same before and after RW-59 |
| `unmeasured` is not defined | It is defined in the SushiSkills format page, and missing from this repository's reference |
| README conflicts will hurt parallel agents | They are real and measured, and rare: 1 merge in 102 |

## Literature

| Source | What it says | What it changes here |
| --- | --- | --- |
| Beads, a git-backed tracker for coding agents | Sequential IDs collided when agents created issues at once; it moved to hash IDs and ships a merge driver | Confirms the hazard. Hash IDs would change every cited ID in 13 repositories; `renumber` stays |
| towncrier, blurb | One file per change, assembled at release, avoids a file every branch edits | Our tables diff per row; the conflicts that remain are the counters and the generated index |
| Merge drivers for lockfiles | Keep one side, then regenerate; the driver is registered per clone | `renumber` already regenerates and needs no per-clone setup |
| git-bug | Stores edit operations, not state, and orders them with logical clocks | Sound, and a different product; not adopted |
| Backlog.md | One Markdown file per task, driven by a CLI and `AGENTS.md` | Same shape as ours; one file per task is the conflict-free variant |
| GitHub closing keywords | A commit message closes an issue by ID when it reaches the default branch | Precedent for closing by ID with no hash |
| `git interpret-trailers` | Trailers are the last paragraph, parsed as `Token: value` | The `Backlog:` line fits the convention |
| "Evaluating AGENTS.md" (arXiv 2602.11988) | Context files tend to lower task success and raise cost by over 20 percent; keep requirements minimal | Supports keeping the backlog's rules few and out of every session when no task needs them |
| IFScale (arXiv 2507.11538) | Instruction following degrades as the instruction count grows, differently by model | Same: each rule has a price |
| METR, "Recent frontier models are reward hacking" | Models modify tests or scoring code to pass; detection undercounts | A check that reads form only, such as `none (<reason>)`, can be gamed. The measured reasons show no sign of it; the report command is how to keep watching |
| Kanban aging and service level expectations | Age limits are usually set from the percentiles of past cycle times | Our 2, 14, 90 and 180 days are fixed; recalibrate once the backlog has data |

## What each finding became

| Finding | Verdict | Action |
| --- | --- | --- |
| Closing needs a hash that does not exist yet | Real, one commit in eight | `close --commit` optional; the line names the ID alone (done) |
| A conflicted or unreadable store gives a cascade of false faults | Real | One fault with its remedy, nothing else (done) |
| `renumber` hides what it rewrote | Real, small | It says so (done) |
| The reference lacks the state meanings and the post-merge steps | Real | Added to `docs/reference/BACKLOG.md` (done) |
| The mark marks a filed entry and lags the hook by one commit | Real | The owner decides; it is an open question of the `BACKLOG` topic |
| `backlog import` has no remaining caller | Measured in 21 local repositories only | The owner decides whether to delete it |
| The trailer cannot cite another repository's entry, and plan jobs are no entries | Real, 43 commits | SushiSkills' checker and skills; handed over below |
| "Take what it gives" is unconditional | Real, read from the text | SushiSkills' template and skill; handed over below |
| Merge conflicts, hash IDs, a merge driver | Rare, 1 in 102 | Not worth a format change; revisit when parallel agents merge daily |
| Age limits | No data | Recalibrate later |

## Handed to SushiSkills

These live in files that repository owns, and this repository holds copies of some. None was
changed here.

1. `check_backlog_trailer.py`: let `Backlog:` cite `<repository> RW-<n>`, the form `Blocked by`
   already uses.
2. The `multi-agent-work` and `backlog` skills: say whether a plan job is a backlog entry. Today
   a third of the `none` commits are plan jobs.
3. `CLAUDE_TEMPLATE.md` and the `backlog` skill: "Session start, when the owner gave no task".
4. `DISPATCH.md`, rule 13: a report heading "Backlog findings", since a worker may not write
   entries and the dispatch names no place for what it found.
5. The priority table is written three times, in the skill, `BACKLOG_FORMAT.md` and this
   repository's reference, in three wordings.
6. `check_all.py` and the hooks: the stamp moves to a post-commit step, if the owner rules so.

## Not measured

- Whether agents file entries less often than they should. The history shows entries named, not
  entries missed.
- The cost of the 75 KB of rules on task success. The studies above measure other repositories.
- Anything outside the thirteen repositories of the workspace.
