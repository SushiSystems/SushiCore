# Changelog

## v0.18.1 — 2026-11-28

- 2026-11-28 — tools: Made the commit-msg hook refuse a commit that changes a path an open work entry's `Source` covers and neither closes nor names that entry in its `Backlog:` line (`backlog/admission.py`, RW-171).
- 2026-11-28 — tools: Made the commit-msg hook refuse a commit that opens more than three work entries on files it changes (`tools/hooks/commit_msg.py`, `backlog/admission.py`, RW-172).
- 2026-11-28 — backlog: Added `backlog here <PATH>...`, which lists the open entries whose `Source` covers a path (`backlog/command_read.py`, RW-173).
- 2026-11-28 — backlog: Dropped the `backlog check` rule that every open design topic is cited by a work entry, and deprecated the `open_designs` argument of `check_backlog` (`backlog/check.py`, RW-174).
- 2026-11-28 — backlog: Added `backlog flow`, which reads from git the work opened, closed, closed the same day and changed but left open in a window (`backlog/flow.py`, `backlog/history.py`, RW-175).
- 2026-11-28 — backlog: Added `backlog stale`, which lists the work past the 14-day triage age with the later commits to its `Source` (`backlog/triage.py`, RW-176).
- 2026-11-24 — code: Tested the ten shared-tool modules that came into the package without a test; the tolerance header test moved to `tests/support/` (`tests/tools/`, RW-170).
- 2026-11-24 — tools: Moved every Sushi library to run the shared checkers from the package, with no copy or lock left in any of them (RW-167).
