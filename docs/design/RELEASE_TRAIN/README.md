# Release train

**Status:** Open — no phase planned yet
**About:** How a SushiCore change reaches every Sushi library without a release of each one
**Modules:** `source/sushicore/shared_tools`

## Problem

A one-line fix in SushiCore took a release of SushiCore and then, in dependency order, a release of
every library, each waiting for CI and for the package index before the next. Three things caused it:

- every library required `sushicore>=X,<next minor`, and a downstream CI job that installs two
  libraries' CLIs side by side failed when their bounds did not meet;
- the shared checkers are copied into each repository under `tools/` and locked by hash, so a fix
  to one of them needs a sync commit and a CI run in every repository;
- the chain is walked by hand.

## Decision

Remove the three causes in turn, one phase each, and keep a manual walk only for a library whose own
public interface breaks.

## Design

R1 drops the upper bound: a SushiCore release needs no release of a library, and a break shows in
that library's CI. R2 runs the checkers with `python -m` from the installed package, so the version a
repository checks with is the one its pin resolves. R3 makes the jobs that test against upstream
install that upstream from source. R4 is a command that does what remains of the walk.

## Phases

| Id | Phase | State |
| --- | --- | --- |
| R1 | Consumers require sushicore with a lower bound only; done in every library at v0.17.1 | built |
| R2 | The shared checkers run from the installed sushicore package instead of copies under tools/, so the lock and the sync commits go | planned |
| R3 | Downstream CI jobs install upstream libraries from their checked-out source under one constraints file, so a pin cannot clash | planned |
| R4 | One command walks the library graph in dependency order: bump, wait for green, tag, wait for the index, go on | planned |

## Open questions

None.
