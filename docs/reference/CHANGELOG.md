# Changelog

## Unreleased

2026-11-17 — testing: Launched only the shard programs a filter can reach, keeping any program newer than its listing, and gave Files a modification time (RW-76, RW-89).
2026-11-17 — shared_tools: Made sync write the shared README rows, name each missing setting with its value, and know the pre-move copies by digest (RW-86, RW-87, KI-33).
2026-11-17 — checking: Tested every ceiling at its edge and the conditions a mutation sample left alive in six checkers (SushiSkills RW-61, RW-62).
2026-11-17 — checking: Walked every checker's tree through walk_files and derived folders through one folders_of (RW-85, `ignored_paths.py`).
- 2026-11-17 — testing: Warned when a slow rerun writes no result file and stopped handing the gate a folder that holds none (RW-63, `slow_rerun.py`).
- 2026-11-17 — cmake_driver: Gave the driver port and the in-memory driver the `resource_spec_file` argument the disk driver takes (RW-63, `cmake_driver_port.py`).

## v0.14.1 — 2026-11-16

- 2026-11-16 — checking: Pruned git-ignored folders before walking them in the comment and probe checkers, so a large ignored tree costs no time (RW-84, `ignored_paths.py`).
- 2026-11-16 — shared_tools: Wrote the header the target's settings build on a shared Python file it did not hold, not upstream's open block (RW-83, `header_merger.py`).
- 2026-11-16 — shared_tools: Left `check_package_layers.py` and `check_config_reads.py`, which read SushiCore's own packages, out of the shared set (RW-82, `sync_service.py`).

