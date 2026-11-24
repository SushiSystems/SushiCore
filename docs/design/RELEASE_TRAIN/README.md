# Release train

**Status:** Open — no phase planned yet
**About:** How a SushiCore change reaches every Sushi library without a release of each one
**Modules:** `source/sushicore/shared_tools`, `source/sushicore/release_train`

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
repository checks with is the one its pin resolves. R3 keeps R1 from coming back: the jobs that test
against upstream already install it from source, so the bound was the only clash, and a checker
now refuses it. R4 is `python -m sushicore.release_train`, which does what remains of the walk: it reads the pins
of the workspace, orders the libraries, and for each one moves its pins, bumps the files its last
release commit changed, closes the changelog, waits for CI, tags, and waits for the release and PyPI.

## Phases

| Id | Phase | State |
| --- | --- | --- |
| R1 | Consumers require sushicore with a lower bound only; done in every library at v0.17.1 | built |
| R2 | The shared checkers run from the installed sushicore package instead of copies under tools/, so the lock and the sync commits go | planned |
| R3 | Downstream CI jobs already install upstream CLIs from their checked-out tags; `check_sushicore_pin.py` refuses an upper bound on sushicore, so their side-by-side install cannot clash again | built |
| R4 | One command walks the library graph in dependency order: bump, wait for green, tag, wait for the index, go on | built |

## Open questions

None.
