# Changelog

## Unreleased

- 2026-11-22 — commands: Ship the shared CMake build policy and the CLI helpers every Sushi C++ repository copies (RW-157).
- 2026-11-22 — commands: Added `sushicore.docker`, the `docker build` and `docker run` of a module's developer image that three module CLIs copied (RW-157, `docker_environment.py`).
- 2026-11-22 — commands: Added `ExecutableIndex.select_interactive`, which asks through the console the index was made with `console=` (RW-157, `discovery.py`).
- 2026-11-22 — provision: Added `RunDirs.for_module`, which keeps a tree's run-time folders in the `.<module>_package_dirs.json` every module CLI names (RW-157, `consumer_build.py`).
- 2026-11-22 — commands: Shipped `SushiBuild.cmake`, the build policy and helpers every Sushi C++ repository copied, and put its folder on the module path of every configure (RW-157, `cmake_modules.py`).
- 2026-11-22 — commands: Removed `lld_linker` and the `platform` argument of `CMakeDriver`, since the build policy of the CMake modules links with lld (RW-157, `cmake_driver.py`).

## v0.15.7 — 2026-11-22

- 2026-11-22 — commands: Linked a Linux configure with lld when its clang or icpx compiler has it, and said so in a line, unless the configure chose a linker (RW-156, `lld_linker.py`).
