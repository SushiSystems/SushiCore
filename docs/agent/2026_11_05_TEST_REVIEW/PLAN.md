# Test review: plan

**Status:** Open — paused by the owner on 2026-11-06; T jobs done, M1 next

Applies the verdicts of `REPORT.md`, in hierarchy order: the shared helpers, adapters and seams the
rewrites need come first, then the defects the review found, then each module's tests. A module job
applies every record of its module: rewrite, resize, split, merge and delete as the record says, and
writes each add. Nothing in a module job changes production code except a seam a job above built.

## Jobs

| Job | Files | Waits on | Status |
| --- | --- | --- | --- |
| T1 | In-memory adapters beside their ports: `proc.Runner`, the console (one recorder replacing every copy), `ConfigModule`, `MachineEnvironment`, `ToolkitLocator`, `IDependencySource`, the git client, the clock (moved out of `package_fakes.py`) |  | done |
| T2 | A file-system port for the backlog and design store, with its in-memory adapter |  | done |
| T3 | `tests/conftest.py` and `pyproject.toml`: the size timeouts, and the autouse fixture that hands every test a temp folder |  | done |
| T4 | The defects of this report, each with a test that fails first |  | done |
| T5 | `tools/testing/check_test_additions.py`, `tools/tests/test_check_test_additions.py` deleted |  | done |
| M1 | the tests of `(root)` (38 files): 133 rewrite, 33 resize, 17 split, 19 merge, 21 delete | T1, T2, T3, T4, T5 | in progress |
| M2 | the tests of `backlog` (9 files): 9 rewrite, 10 resize, 19 split, 1 delete | T1, T2, T3, T4, T5 | done |
| M3 | the tests of `design` (7 files): 7 rewrite, 2 resize, 14 split, 1 delete | T1, T2, T3, T4, T5 | todo |
| M4 | the tests of `docs_bundle` (13 files): 11 rewrite, 30 resize, 6 split, 6 merge, 3 delete | T1, T2, T3, T4, T5 | todo |
| M5 | the tests of `help` (5 files): 1 split, 10 merge, 1 delete | T1, T2, T3, T4, T5 | todo |
| M6 | the tests of `provision` (40 files): 154 rewrite, 62 resize, 10 split, 8 merge, 13 delete | T1, T2, T3, T4, T5 | todo |
| M7 | the tests of `provision/gpu` (26 files): 76 rewrite, 6 resize, 12 merge, 21 delete | T1, T2, T3, T4, T5 | todo |
| M8 | the tests of `provision/sushi_packages` (25 files): 58 rewrite, 17 resize, 3 split, 3 merge, 12 delete | T1, T2, T3, T4, T5 | todo |
| M9 | the tests of `provision/test_download_verifier` (2 files): 13 rewrite, 3 resize, 1 delete | T1, T2, T3, T4, T5 | todo |
| M10 | the tests of `provision/test_fragments` (3 files): 16 rewrite, 2 delete | T1, T2, T3, T4, T5 | todo |
| M11 | the tests of `provision/test_steps` (4 files): 32 rewrite, 2 merge | T1, T2, T3, T4, T5 | todo |
| M12 | the tests of `provision/toolchains` (4 files): 38 rewrite, 6 merge, 2 delete | T1, T2, T3, T4, T5 | todo |
| M13 | the tests of `test_deps_fragment` (2 files): 3 rewrite, 6 resize, 1 delete | T1, T2, T3, T4, T5 | todo |
| M14 | the tests of `test_renderer` (3 files): 13 rewrite, 10 merge, 1 delete | T1, T2, T3, T4, T5 | todo |
| M15 | the tests of `test_workspace` (3 files): 1 merge, 1 delete | T1, T2, T3, T4, T5 | todo |
| M16 | the tests of `testing` (6 files): 9 resize, 7 split, 2 delete | T1, T2, T3, T4, T5 | todo |
| M17 | the tests of `tools` (2 files): 6 resize, 1 split, 5 delete | T1, T2, T3, T4, T5 | todo |
| M18 | the tests of `ui` (8 files): 13 rewrite, 3 split, 13 merge, 9 delete | T1, T2, T3, T4, T5 | todo |

## Acceptance

- **T1.** Each adapter keeps its port's promise with no subprocess, terminal or disk, and other repositories' CLI tests can import it. Build: `python -m pytest` through the repository's test command.
- **T2.** Backlog and design logic is tested small with no disk. Build: the repository's test command.
- **T3.** The timeouts equal the skill's; a small test gets no temp folder unless it asks. Build: the repository's test command.
- **T4.** Every defect above is fixed or has a backlog entry. Build: the tests of each touched module.
- **T5.** Neither file exists and the checkers pass. Build: `python tools/check_all.py .`
- **M jobs.** Every record of the module is applied: no test the report deletes remains, every kept and
  new test passes at the size its label states, and the module's tests pass through the project's own
  test command. Build: that command over the module.

T1 comes first in every repository's plan: sushilog, sushiprofiler, sushitrack, sushidsp and sushistack
wait on it for their CLI tests. The owner chooses inline or parallel mode.
