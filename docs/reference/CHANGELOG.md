# Changelog

## Unreleased

- 2026-11-24 — tools: Moved every Sushi library to run the shared checkers from the package, with no copy or lock left in any of them (RW-167).

## v0.18.0 — 2026-11-24

- 2026-11-24 — tools: Moved the shared checkers into the package as `sushicore.tools`, run with `python -m sushicore.tools check .`; the copies, the lock and `shared_tools` sync are gone (`source/sushicore/tools/`, RW-167).
- 2026-11-24 — release_train: Added `python -m sushicore.release_train`, which releases a library and every library that pins it in order, waiting for CI, the release and PyPI (`release_train/`, RW-169).
- 2026-11-24 — tools: Added `check_sushicore_pin.py`, which refuses an upper bound on the sushicore requirement, so CLIs installed side by side cannot clash on it (`tools/checking/check_sushicore_pin.py`, RW-168).
