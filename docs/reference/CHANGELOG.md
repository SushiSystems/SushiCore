# Changelog

## Unreleased

- 2026-11-28 — tools: Made the commit-msg hook refuse a commit that changes the `Source` of an open work entry and neither closes nor names it in its `Backlog:` line (`tools/hooks/commit_msg.py`, `backlog/admission.py`, RW-171).
- 2026-11-28 — tools: Made the commit-msg hook refuse a commit that opens more than three work entries on files it changes (`tools/hooks/commit_msg.py`, `backlog/admission.py`, RW-172).
- 2026-11-28 — backlog: Added `backlog here <PATH>...`, which lists the open entries whose `Source` covers a path (`backlog/command_read.py`, RW-173).
- 2026-11-28 — backlog: Dropped the `backlog check` rule that every open design topic is cited by a work entry, and deprecated the `open_designs` argument of `check_backlog` (`backlog/check.py`, RW-174).
- 2026-11-28 — backlog: Added `backlog flow`, which reads from git the work opened, closed, closed the same day and changed but left open in a window (`backlog/flow.py`, `backlog/history.py`, RW-175).
- 2026-11-28 — backlog: Added `backlog stale`, which lists the work past the 14-day triage age with the later commits to its `Source` (`backlog/triage.py`, RW-176).
- 2026-11-24 — code: Tested the ten shared-tool modules that came into the package without a test; the tolerance header test moved to `tests/support/` (`tests/tools/`, RW-170).
- 2026-11-24 — tools: Moved every Sushi library to run the shared checkers from the package, with no copy or lock left in any of them (RW-167).

## v0.18.0 — 2026-11-24

- 2026-11-24 — tools: Moved the shared checkers into the package as `sushicore.tools`, run with `python -m sushicore.tools check .`; the copies, the lock and `shared_tools` sync are gone (`source/sushicore/tools/`, RW-167).
- 2026-11-24 — release_train: Added `python -m sushicore.release_train`, which releases a library and every library that pins it in order, waiting for CI, the release and PyPI (`release_train/`, RW-169).
- 2026-11-24 — tools: Added `check_sushicore_pin.py`, which refuses an upper bound on the sushicore requirement, so CLIs installed side by side cannot clash on it (`tools/checking/check_sushicore_pin.py`, RW-168).
