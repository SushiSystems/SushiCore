# Changelog

## Unreleased

- 2026-11-22 — commands: Added `--report` to the shared `build` command, as every CLI declares it (RW-159, `build_command.py`).
- 2026-11-22 — commands: Added `--type` to the shared `run` command, which now takes the build types of the CLI (RW-159, `run_command.py`).
- 2026-11-22 — commands: Added the shared `build` and `run` commands, which a CLI registers with a service of its own (RW-158, `build_command.py`).
- 2026-11-22 — commands: Added the shared `bench` and `check` commands, each calling a service the CLI supplies (RW-158, `check_command.py`).
- 2026-11-22 — commands: Added the shared `--sanitize` option, which takes the kinds `sushi_sanitizers` builds as one set (RW-158, `sanitize_option.py`).
- 2026-11-22 — commands: Added the help panels, the canonical verb list and `assert_registers_verbs`, which fails a CLI's test that lacks a verb (RW-158, `verbs.py`).
- 2026-11-22 — provision: The deprecated names promised for removal in 0.16.0 are now promised for removal in 0.17.0, since RW-117, RW-118 and RW-119 stay open (RW-117, RW-118, RW-119, `windows_installer.py`).
- 2026-11-22 — commands: Ship the shared CMake build policy and the CLI helpers every Sushi C++ repository copies (RW-157).
- 2026-11-22 — commands: Added `sushicore.docker`, the `docker build` and `docker run` of a module's developer image that three module CLIs copied (RW-157, `docker_environment.py`).
- 2026-11-22 — commands: Added `ExecutableIndex.select_interactive`, which asks through the console the index was made with `console=` (RW-157, `discovery.py`).
- 2026-11-22 — provision: Added `RunDirs.for_module`, which keeps a tree's run-time folders in the `.<module>_package_dirs.json` every module CLI names (RW-157, `consumer_build.py`).
- 2026-11-22 — commands: Shipped `SushiBuild.cmake`, the build policy and helpers every Sushi C++ repository copied, and put its folder on the module path of every configure (RW-157, `cmake_modules.py`).
- 2026-11-22 — commands: Removed `lld_linker` and the `platform` argument of `CMakeDriver`, since the build policy of the CMake modules links with lld (RW-157, `cmake_driver.py`).

## v0.15.7 — 2026-11-22

- 2026-11-22 — commands: Linked a Linux configure with lld when its clang or icpx compiler has it, and said so in a line, unless the configure chose a linker (RW-156, `lld_linker.py`).
