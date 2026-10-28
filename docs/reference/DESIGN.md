# Design topics

A design topic is the folder `docs/design/<TOPIC>/`, whose `README.md` says what is being built
and why. One subject has one topic, and one module belongs to one topic. The `design` commands
open topics, pages and phases, and find and merge the topics that describe one subject. Every
module CLI registers the group (`sr design new`); a repository without a CLI runs
`python -m sushicore.design`. The code is
[`sushicore.design`](../../source/sushicore/design/README.md).

## The frame

```
# <Title>

**Status:** Open — phases A2, A3 to be built
**About:** One sentence saying what the topic is.
**Modules:** `modules/atmosphere`, `modules/presentation/clouds`

## Problem
## Decision
## Design
## Phases
## Open questions
```

The tool writes the frame: the title, the status line, the metadata lines, the five headings and
the phase table. The prose inside a section is the author's. The format of each part is the
design format of the SushiSkills `documentation` skill.

## Ownership

Every topic names its modules on a `**Modules:**` line, or the word `none` for a subject with no
code, such as a release; a topic of no module carries an `**About:**` line. A module path is named
by at most one topic. A path inside a module belongs to the topic that names the deepest module
holding it.

`design new` refuses a module that another topic names, or one that lies inside or around a
module another topic names, and names that topic. A subject such as clouds, inside the
atmosphere's modules, is a page of `ATMOSPHERE`, not a topic: topics have two levels, the topic
and its pages and phases.

## Commands

| Command | Does |
| --- | --- |
| `design list [--json]` | Every topic with its status, its modules and its open phases |
| `design show <TOPIC>` | The topic's document, and its pages listed |
| `design owner <path>` | The topic that owns the module holding the path, or `none` |
| `design new <TOPIC> --modules <paths> --about <text>` | Writes the topic with its frame; refuses an owned module |
| `design page <TOPIC> <PAGE>` | Adds an empty page beside the topic's `README.md` |
| `design phase <TOPIC> <Id> <text>` | Adds a planned phase; a shipped topic opens again |
| `design phase-state <TOPIC> <Id> <state>` | Moves a phase; the topic is `Shipped` once every phase is `built` or `withdrawn` |
| `design overlap [--json]` | Every module two topics name, every named module inside another's, and topic names that share a word |
| `design merge <INTO> <FROM>` | Makes `FROM` a page of `INTO` and deletes `FROM` |
| `design check` | Checks every rule below |

## Merge

`design merge INTO FROM`:

- writes `FROM`'s document, without its status, metadata and phase table, as the page `FROM.md`
  in `INTO`'s folder, and moves `FROM`'s other pages beside it, a page whose name `INTO`
  already uses taking `FROM_` in front;
- appends `FROM`'s phases to `INTO`'s table, an id `INTO` already uses taking `FROM-` in front;
- joins the modules of both on `INTO`'s `**Modules:**` line, and opens `INTO` again when a joined
  phase is still to be built;
- rewrites `FROM#<phase>` and `FROM` on the `**Implements:**` and `**Designs:**` lines of every
  work folder;
- deletes `FROM` and rewrites every citation of its files in the manual and the source, printing
  each citation it cannot place.

The generated views of the documentation tools, such as the topic map, are written by those tools
afterwards.

## Check

`design check` fails:

- a design document loose in `docs/design/`;
- a `##` section that is not one of the five, one missing, and the five out of order;
- a status line longer than 160 characters;
- a `## Phases` section without its table or `None.`, a table with other columns, and a phase
  state that is not `planned`, `building`, `built` or `withdrawn`;
- a commit hash, and a line outside the status that dates when work was built, merged or reviewed;
- a topic without a `**Modules:**` line, and a topic of no module without an `**About:**` line;
- a module path that is not in the repository;
- a module two topics name;
- an `**Implements:**` or `**Designs:**` item of a work folder that names no topic or phase.
