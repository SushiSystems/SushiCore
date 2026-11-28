# Changelog

## v0.18.2 — 2026-11-28

- 2026-11-28 — tools: Made the git reader of the shared checkers read a byte that is not UTF-8 as U+FFFD, so `check_test_value` reads the diff of a Latin-1 file (`commits/history.py`).
- 2026-11-28 — backlog: Moved SushiEngine onto sushicore 0.18.1 and closed the 50 design-copy entries it held (RW-178), and took its three checker entries as RW-204 to RW-206 (`docs/backlog/CHECKERS.md`).
- 2026-11-28 — backlog: Took the 25 checker entries SushiSkills held, as RW-179 to RW-203 in a new `CHECKERS` area, each with its source file in this package (`docs/backlog/CHECKERS.md`).
- 2026-11-28 — provision: Made the Windows probe plan search for icx and rc through its injected glob seam, not the module's own glob search; PATH still comes before the glob for rc (`provision/probe_plans/windows.py`, RW-164).
