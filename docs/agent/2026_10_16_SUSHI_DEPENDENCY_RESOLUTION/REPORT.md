# Report: Sushi dependency resolution

Status: done. Written by one subagent (opus, low) in two rounds; the orchestrator removed one
unused import and ran the verification below.

## Verification

```
$ python -m pytest -q -m "small or medium"
1130 passed in 19.02s
$ python tools/check_all.py .
clean: 9 checkers, tests
```

## What it does

- A fragment pins each Sushi library in `[sushi.<name>]`, with `version` (a tag) and `commit`
  (40 hex). A pin not listed in `depends_on` is an error. A module listed without a pin still
  reads: it resolves through `<NAME>_DIR` and the sibling only, is never fetched, and `doctor`
  warns that it is not pinned.
- `provision/sushi_sources.py` resolves a library in the order `<NAME>_DIR`, `../<name>`,
  `<home>/sources/<name>/<version>/`, and says which it used.
- `provision/sushi_fetch.py` clones a pinned tag that is missing, shallow and tag only, checks
  HEAD against the pin and removes the folder on a mismatch. A failed clone names the library,
  the URL, the tag and the `<NAME>_DIR` way out.
- `provision/pin_chain.py` walks the pins through each resolved library's fragment and reports a
  library pinned at two versions, with both pinning repositories; `setup` stops on it before any
  clone.
- `provision/sushi_setup.py` runs conflict check, fetch and recheck for `setup`;
  `provision/module_checks.py` assembles the `doctor` rows; `sushi_source_check.py` holds the
  three new rows.
- `StackConfig.sushi_definitions` gives CMake `-D<NAME>_DIR=<path>` for each resolved pin.

Every behaviour has a test in the file that mirrors its module under `tests/provision/`, plus
`tests/test_deps_fragment/` and `tests/test_stack_config.py`.

## Not done

- No consumer passes `sushi_definitions` to CMake yet; tasks 7 to 10 of the SushiLog plan
  switch each repository over.
- A library pinned only by a fetched library is checked for conflicts but not cloned.
- `locate_sibling` with a configured `<name>_dir` that does not exist now falls through to the
  sibling and the fetched copy; before, it returned None.
- No real clone was run; the end-to-end check waits for SushiRuntime to pin SushiLog.

## SOLID breaches and unneeded dependencies

- Kept: `provision/commands.py` (334 lines) still holds the setup and doctor command bodies
  beside the command registration. Recorded in `REMAINING_WORK.md`.
- Kept: `StackConfig.fragment` and `ModuleProvision.fragment` declare one path twice, joined
  only by a shared default. Recorded in `REMAINING_WORK.md`.
- Seen: `provision/git_client.py` sits at layer 4 only to reuse `packages/base.run`, a process
  helper that belongs below the package managers. Recorded in `REMAINING_WORK.md`.
- Fixed: an unused `ToolchainSelection` import in `commands.py`, a duplicate `project_root()`
  call and a fixed fragment path in `StackConfig.sushi_pins`.
- Fixed after the release review: `present_toolchains` moved to `probe.toolchain_presence`, so
  `setup` no longer depends on the doctor-row module; one fragment reader
  (`deps_fragment.read_present`, `pins_at`) serves `commands`, `sushi_setup` and `StackConfig`;
  `PinConflict` no longer names a consumer command.

## Release review

A reviewer read the manual against the code for v0.9.1 and found 17 false or stale sentences,
six humanizer breaks, a changelog line missing the new public names, and three SOLID breaches.
All were fixed in a third round; the orchestrator re-checked the changed lines.
- Unneeded dependencies made: none.
