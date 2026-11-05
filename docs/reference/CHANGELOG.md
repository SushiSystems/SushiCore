# Changelog

## Unreleased

- 2026-11-05 — testing: Added in-memory adapters for the runner (with a `CommandRunner` protocol), console, config module, git client, dependency source, toolkit locator, machine environment and package clock (`proc_memory.py`).
- 2026-11-05 — tools: Took the shared checkers of 2026-11-05 with a baseline of the findings they meet, which RW-64 clears.
## v0.10.11 — 2026-11-02

- 2026-11-02 — commands: Shuffle the test order by default in the shared test command, print the seed and take `--seed` and `--no-shuffle` (`sushicore.testing`).
- 2026-11-02 — commands: Print "(not rebuilt)" on the budget line of a run that did not rebuild, and never gate it (`sushicore.testing`).
