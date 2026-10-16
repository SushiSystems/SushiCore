# Sushi dependency resolution

Task 6a of SushiSkills `docs/agent/2026_10_16_SUSHILOG_REPOSITORY/PLAN.md`: a Sushi library a
repository links resolves without a SushiStack workspace. The contract is SushiSkills
`skills/dependencies/SKILL.md`, section "A Sushi library as a dependency".

## Units

| Unit | Layer | Does |
| --- | --- | --- |
| `deps_fragment.py` | outside `provision` | Reads `[sushi.<name>]` pins and checks them against `depends_on` |
| `provision/home.py` | 0 | Adds `sources_dir()` |
| `provision/sushi_sources.py` | 1 | Resolves `<NAME>_DIR`, then `../<name>`, then `<home>/sources/<name>/<version>` |
| `provision/pin_chain.py` | 2 | Walks the pins through each resolved library's fragment and finds a library pinned twice |
| `provision/git_client.py` | 4 | Clones one tag shallow and reads HEAD |
| `provision/sushi_fetch.py` | 5 | The setup step that clones each pin with no directory or sibling and checks its commit |
| `provision/sushi_source_check.py` | 5 | The doctor rows: the source per pin, and the pin conflicts |
| `provision/sushi_setup.py` | 5 | Reads the own pins, the locate fallback, and conflict check, fetch, recheck |
| `provision/module_checks.py` | 5 | Assembles the doctor rows of a module |
| `provision/commands.py` | 6 | Calls the two above from `setup` and `doctor` |
| `stack_config.py` | outside `provision` | `locate_sibling` through the resolver, and `sushi_definitions` for CMake |

## Acceptance

A scratch layout holding only a consumer whose fragment pins one library: "fetched" after the
step runs with a fake git, "sibling" with a sibling and the step skipped, "directory" with
`<NAME>_DIR` set; a commit mismatch fails the step and leaves no folder. Added by the
coordinator: a failed clone names the URL, the tag and `<NAME>_DIR`; a three-level chain with
and without a pin conflict.
