# Backlog

The backlog of a repository is its remaining work and its known issues, kept as tables in
`docs/backlog/` and changed only through the `backlog` commands. Every module CLI registers the
group (`se backlog next`); a repository without a CLI runs `python -m sushicore.backlog`. The code
is [`sushicore.backlog`](../../source/sushicore/backlog/README.md).

## The store

```
docs/backlog/
    README.md          generated: each area counted by state and priority, and the pins
    backlog.toml       the areas and the owner's pins
    ids.toml           the next number of each kind and every number ever closed
    <AREA>.md          one file per area, holding both tables
    detail/<ID>.md     the explanation of an entry that does not fit its row
```

An area file:

```
# Physics

## Remaining work

| ID | Pri | State | Title | Done when | Blocked by | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RW-461 | P1 | decision | Choose the matter solver route | The owner has chosen AVBD or XPBD |  | `docs/design/PHYSICS/README.md` | 2026-10-21 |

## Known issues

| ID | Origin | Symptom | Workaround | Fix | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- |
| KI-31 | own | The cantilever wave runs 1.83 times too fast | none | none, waits on RW-461 |  | 2026-10-21 |
```

| Column | Rule |
| --- | --- |
| `ID` | `RW-<n>` or `KI-<n>`, taken from `ids.toml`; a closed number is never used again |
| `Pri` | `P0`, `P1`, `P2` or `P3` |
| `State` | `decision`, `open`, `blocked` or `unmeasured` |
| `Title` | What is to be done, as an imperative sentence; at most 90 characters |
| `Done when` | One acceptance criterion; at most 160 characters |
| `Blocked by` | Filled when the state is `blocked` and only then: IDs, `<repository> RW-<n>`, or `external: <reason>` |
| `Source` | Empty, or one path from the repository root in backticks with an optional `§<n>`; the path exists |
| `Origin` | `own`, `toolchain`, `dependency`, or a sibling's issue written `<repository> KI-<n>` |
| `Symptom` | The symptom as a reader meets it; at most 90 characters |
| `Workaround` | What a reader does, or `none`; at most 160 characters |
| `Fix` | `RW-<n>`, or `none, <reason>`; required when the origin is `own` |
| `Opened` | The ISO date the entry was written |

Rows are sorted by ID and a pipe inside a cell is written `\|`, so a change to one entry is a
one-line diff. An own issue with no workaround and a fix in the backlog is work alone: it lives in
the remaining work table, not in both.

## Priority and order

| Priority | Means | Age limit |
| --- | --- | --- |
| P0 | Data loss, a broken gate, a regression in a release, a security fix after disclosure | 2 days |
| P1 | A defect with no workaround, or work that blocks other work | 14 days |
| P2 | A defect with a workaround, or a missing check that let a defect through | 90 days |
| P3 | An improvement | 180 days, then reviewed |

An entry past its limit is late. `backlog next` returns, in order: the owner's pins that are
ready, in their listed order; then every other ready entry by priority, then the oldest first,
then by ID. An entry is ready when it is `open` or `unmeasured`, or `blocked` only by entries of
this repository that are closed. A `decision` is never returned; `backlog decisions` lists them.
The pins are at most ten IDs in `backlog.toml`.

## Commands

| Command | Does |
| --- | --- |
| `backlog list [--area A] [--state S] [--priority P0..P1] [--kind work\|issue] [--late] [--json]` | Lists entries |
| `backlog show <ID> [--json]` | Prints an entry and its detail file |
| `backlog next [--count n] [--json]` | Prints the work to take, first to last |
| `backlog decisions [--json]` | Lists the entries waiting for the owner |
| `backlog add work --area A --priority P --title T --done-when D [--source S] [--blocked-by IDS] [--decision]` | Adds work and prints its ID |
| `backlog add issue --area A --origin O --symptom T --workaround W [--fix F] [--source S]` | Adds a known issue and prints its ID |
| `backlog promote <KI-n> --priority P --title T --done-when D` | Opens work from an issue and writes its ID into the issue's `Fix` |
| `backlog set <ID> <column> <value>` | Changes one column |
| `backlog move <ID> <AREA>` | Moves an entry to another area |
| `backlog close <ID> --commit <hash>` | Deletes the entry, its detail and its pin, records the ID as closed, and prints its changelog line |
| `backlog pin <ID> [--at n]`, `backlog unpin <ID>` | Changes the pins |
| `backlog area list`, `backlog area add <AREA>`, `backlog area merge <INTO> <FROM>` | Lists, adds or merges areas |
| `backlog renumber [--target main]` | Gives each entry that shares an ID with a different one the next free number |
| `backlog import` | Moves the retired files into the store, once |
| `backlog check [--report]` | Checks every rule below; `--report` also lists the late work |

Every change refuses a value that breaks a rule of its kind, writes the files it touched and
regenerates `README.md`. `close` refuses an ID another open entry cites in `Blocked by`, `Fix` or
`Origin`; its changelog line is for the caller to write into `CHANGELOG.md`. A refusal is a
`BacklogError`, which a CLI prints as one line.

## Two branches, one ID

Two branches that each add an entry take the same number, and the merge conflicts in `ids.toml`
and in the area file. `backlog renumber` reads both sides of the conflict, keeps the ID on the
entry the target branch holds, gives the other the next free number and prints each change. The
prose that cites the renamed ID is the caller's to rewrite.

## Import

`backlog import` reads `docs/design/REMAINING_WORK.md` and `docs/reference/KNOWN_ISSUES.md`, the
form the store replaced, and deletes them:

- Each `## <Area>` section becomes an area: its words in upper case, small words dropped. The
  entries of `## Decisions waiting for the owner` go to `GENERAL`.
- The IDs stay. The counter is the old `Next id:`; every lower number without an entry is closed.
- The IDs of `## Next` become the pins and take `P1`; every other entry takes `P2`.
- `Opened` is the date git blames on the entry's heading.
- An entry whose prose, extra fields or overlong values do not fit its row keeps all of them in
  `detail/<ID>.md`; the row holds the values cut at a word.
- An issue of a sibling's origin takes `<repository> KI-<n>` from its `Upstream:`.
- Every citation of the two files in a Markdown page is rewritten to `docs/backlog/README.md`.
  A source or build file that names one is listed for its author to change.

## Check

`backlog check` fails:

- either retired file still in the repository;
- a configuration, a counter file or an area file that cannot be read, and an area file that is
  not in the shape the tool writes;
- a file in `docs/backlog/` that is not an area named in `backlog.toml`, and an area name that is
  not upper case words joined by `_`;
- a value that breaks its column's rule;
- an ID used twice, at or past its counter, or already closed;
- a `Source` path that does not exist;
- a cited ID that names no open entry here, or in a sibling checked out beside the repository;
- a `blocked` entry whose blocks are all closed;
- a table whose rows are not sorted;
- more than ten pins, and a pin that names no open work or names a decision;
- a detail file whose entry is closed;
- a `README.md` that is not what the entries say;
- an `Open` design topic, outside `_REVISION/`, that no work entry's `Source` cites.

A repository without `docs/backlog/` and without the retired files has nothing to check.
