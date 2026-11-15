# Changelog

## Unreleased

- 2026-11-16 — shared_tools: Left `check_package_layers.py` and `check_config_reads.py`, which read SushiCore's own packages, out of the shared set (RW-82, `sync_service.py`).

## v0.14.0 — 2026-11-16

- 2026-11-16 — checking: Added `check_shared_tools.py`, which fails `check_all` when a shared tool differs from `tools/shared_tools.lock` or the lock is missing (RW-81, `check_shared_tools.py`).
- 2026-11-16 — code: Held every shared checker here, merged with the SushiSkills copy (RW-79, `8e2b0b6`).
- 2026-11-16 — shared_tools: Added `python -m sushicore.shared_tools` with `sync` from a SushiCore tag, `tools/shared_tools.lock` and `check`, in place of the retired copier (RW-80, `shared_tools/`).
- 2026-11-14 — provision: Compiled the Windows adapter build with the toolchain's `clang-cl` and `lld-link` instead of MSVC `cl` (`adapter_builder.py`).
- 2026-11-14 — provision: Applied the patches a backend spec names before configuring the adapter, shipped the CUDA event-anchor patch and stamped it as `<commit>+p<digest>` (`adapter_builder.py`).
- 2026-11-12 — aliases: Let `AliasTable` take the stream and the variables its notices use, so a CLI test reads a notice from memory (`aliases.py`).

