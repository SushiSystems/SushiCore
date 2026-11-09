# Changelog

## Unreleased

## v0.11.0 — 2026-11-10

- 2026-11-10 — provisioning: Changed `ModuleProvision` to take one `MachineSeams` value in place of its three builders; callers pass `seams` (`module_provision.py`).
- 2026-11-10 — testing: Moved `free_memory_mb` and its reserve constant out of `build_gate.py` into `memory_reading.py`, which the gate and the test job count both read.
- 2026-11-10 — testing: Made `test` run one job per core, lowered to fit the free memory, when no `--jobs` is given, and print the count (R1, `job_count.py`).
- 2026-11-10 — provisioning: Fixed 11 provision tests that failed on Windows: the migration plan reads the working directory by probe, and a configured library directory naming no folder yields to the variable (KI-27, `5f66b8f`).
- 2026-11-07 — continuous_integration: Gave the Files port a remove call and routed the backlog check, close and merge through it, so their small tests read no disk (RW-70, `f44d1ef`).
