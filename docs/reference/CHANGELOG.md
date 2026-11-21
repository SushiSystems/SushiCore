# Changelog

## Unreleased

- 2026-11-21 — tools: Skipped `__pycache__` folders by name in the test mirror checker, so a tree without git ignore data reports no finding for them (RW-115, `check_test_mirror.py`).
- 2026-11-21 — clean: Added `register_clean_command`, the one `clean` of every CLI, which removes build trees only with `--yes` (RW-135, `f7eae08`).
- 2026-11-21 — discovery: Made the picker choose nothing and say so when its input has ended or Ctrl+C stops it, so a script with no terminal does not hang.
- 2026-11-21 — run: Added `pick_option`, `list_all_option`, `old_pick_option` and `run_program`, so a `run` command declares and starts a program the same way in every CLI.
- 2026-11-21 — tools: Ran the pre-commit checks on the files the commit will hold, written from the index to a throwaway folder, so a red file on disk cannot refuse a commit that lacks it (RW-134, `pre_commit.py`).
- 2026-11-21 — tools: Let the `Backlog:` line cite an entry of a sibling repository as `<repository> <ID>`, which the commit-msg hook checks when the sibling is checked out (RW-132, `check_backlog_trailer.py`).
- 2026-11-21 — tools: Judged `git commit --amend` against the parent of the commit it replaces, so the hook accepts an amend of a commit that closed its entry (RW-132, `commit_msg.py`).
- 2026-11-21 — backlog: Stopped a sibling's entry and an ID inside a `none (...)` reason from marking an entry unverified here (RW-132, `unverified.py`).
- 2026-11-21 — backlog: Deprecated `backlog import` and `BacklogImporter` since 0.15.0, after removing them broke the shared tests of the twelve repositories that carry the tools; they go in 0.16.0 (RW-133, `importer.py`).
- 2026-11-21 — provisioning: Kept each build unit's last measured peak with its kind, so a kind's reservation follows the units it holds now (RW-130, `unit_peaks.py`).
- 2026-11-21 — backlog: Registered each command through its own function in `command_read.py` and `command_write.py` around one `CommandContext`, so no function of `commands.py` passes 60 lines (RW-91, `commands.py`).
- 2026-11-21 — aliases: Added `AliasTable.flag_announcer()`, the callback of a hidden old flag, so a renamed flag is one hidden option that announces its replacement.
- 2026-11-21 — backlog: Stopped a commit that changes only the backlog and the changelog from marking the entries it names unverified, reading each commit's paths (RW-129, `unverified.py`, `verification.py`).
- 2026-11-21 — backlog: Moved `BacklogRenumberer` and `RenumberResult` out of `importer.py` into `renumber.py`, so no file of the package holds two jobs (RW-128, `renumber.py`).
- 2026-11-21 — backlog: Made --commit optional on close, reported a conflicted or unreadable store as one fault and made renumber say what it rewrote (RW-127, `editor.py`, `check.py`).
- 2026-11-21 — discovery: Made `run --sort` offer the built examples, each with its description, through `ExampleCatalog` (RW-125, `5f73103`).
- 2026-11-17 — downloads: Verify shell pipelines and clones (RW-45, `30a7169`).
- 2026-11-17 — code: Remove hidden module state and apply the class-shape rules (RW-36, `d3f6a0e`).
- 2026-11-17 — tests: Reached code only through public names, making the direct-download installers and build_gate's read_state public (RW-35, `03bb347`).
- 2026-11-17 — docs: Gave every public symbol a docstring of at most eight lines (RW-32, `db0088a`).
- 2026-11-17 — code: Moved the dependency home, the download verifier and the theme and icon presets into objects, deprecating their binders, and marked leaf classes final (RW-36, `e5b724e`).
- 2026-11-17 — code: Split probe, workspace, pipeline, doctor, packages.linux, system and the console builder into one-job modules, keeping the moved names importable with a warning (RW-33, `74a616d`).
- 2026-11-17 — code: Typed the build-side seams the audit named with narrow console and config protocols (RW-34, `fcb14fd`).
- 2026-11-17 — console: Kept a config_dir that raises SystemExit meaning "outside a checkout" for one release, with a deprecation warning (RW-119, `cli_console.py`).
- 2026-11-17 — provision: Restored provision.steps, prime_sudo, packages.run, the gh_latest helpers and the adapter runner names as deprecated shims for one release (RW-118, RW-119, `83edf89`).
- 2026-11-17 — provision: Restored CapturedRun, capture_command and run_command in package_install as deprecated helpers over proc.Runner; they go in 0.17.0 (RW-117, `captured_run.py`).
- 2026-11-17 — errors: Derived every package error from SushiCoreError, raised named errors for bare built-ins and failure returns, and made find_project_root raise ProjectRootNotFoundError (RW-26, `20e3898`, `acb27b9`).
- 2026-11-17 — provision: Carried the console from ModuleProvision; bind_console is deprecated for ModuleProvision(console=...), and _output and bound_memory_console are removed (RW-30, `dacda98`).
- 2026-11-17 — provision: Put intel-llvm, AdaptiveCpp and oneAPI behind one Toolchain contract and registry that shares ToolkitFinder with the GPU backends (RW-31, `af87062`).
- 2026-11-17 — provision: Replaced the target-keyed tables of install, uninstall, probe, managers and the AdaptiveCpp LLVM with per-target plan files a registry finds (RW-24, `600bb48`).
- 2026-11-17 — provision: Moved the branches on the run's target platform behind ITarget, picked once by target_of (RW-24, `provision/target/`).
- 2026-11-17 — provision: Moved what differs by operating system behind IHost and the apt-only steps behind LinuxPackageManager methods, chosen once each (RW-24, `provision/host/`).
- 2026-11-17 — console: Took the line level from the call, and made config, env and the executable picker emit table and prompt events (RW-29, RW-30, `renderer.py`).
- 2026-11-17 — provision: Kept the NVCC and rc.exe glob tables and the first-match helper once, in probe.py (RW-28, `f7b3ae3`).
- 2026-11-17 — proc: Ran every child process in source/ through CommandRunner, so tests use RecordingRunner and no module calls subprocess but proc.py (RW-27, `078e7cd`).
- 2026-11-17 — proc: Made Runner the one process brick, with run_drained and run_quiet, and sent a child's output to the console as events in machine mode (RW-27, `078e7cd`).
- 2026-11-17 — provision: Pinned cmake, git, ninja, doxygen and intel-llvm in base.deps.toml with a version, a url and a sha256, and removed the gh_latest helpers (RW-44, `390e839`).
- 2026-11-17 — provision: Moved run from packages/base.py into process_run.py at layer 1, so git_client sits at layer 2 (RW-23, `b5c0b34`).
- 2026-11-17 — provision: Made setup fetch, round by round, every Sushi library a fetched library pins, refusing two versions of one (RW-18, `6b8cb0b`).
- 2026-11-17 — provision: Refused to remove the portable cmake or doxygen folder under a root is_removable_root does not accept (RW-92, `c90587c`).
2026-11-17 — provision: Asked before accepting any third-party licence, split the steps into one file each, and split the clock into wall and monotonic ports (RW-46, RW-20, RW-66).
2026-11-17 — provision: Deprecated gpu/windows_installer.py, which nothing here calls; it has no replacement and is removed in 0.16.0 (RW-7).
2026-11-17 — backlog: Marked open work a commit named after the last green check_all as unverified, from a stamp check_all writes (RW-59, `verification.py`).
2026-11-17 — design: Printed design and backlog output through force_utf8, so a cp1252 console no longer fails on an arrow (KI-32).
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

