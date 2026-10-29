# Changelog

## Unreleased

- 2026-10-29 — sushi_packages: Fixed a nested package build recompiling the whole library whenever a package below it changed; a handed-down package reaches its flags through a stable link, not its digest folder (`package_resolver.py`).
## v0.10.4 — 2026-10-29

- 2026-10-29 — toolchain: Fixed `c_compiler_for` handing icpx to the C slot; it gives oneAPI's icx beside it, and looks a bare name up on the PATH (`toolchain_args.py`).
