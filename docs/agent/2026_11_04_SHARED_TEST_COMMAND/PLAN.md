# Shared test command: plan

**Status:** Open — gap map done; jobs F1 to F9 next, F2 and F6 wait for the owner

Carries out phase F of the `TEST_PIPELINE` topic of SushiSkills
(`D:/Projects/sushiskills/docs/design/TEST_PIPELINE/README.md`): the test command every module CLI
registers, so it runs tests the way "Running fast", "Time" and "Determinism" in the `testing` skill
say. Parallel mode, at most four subagents, models from `model-routing`.

## Where the command stands

Read on 2026-11-04 from `source/sushicore/testing/` on `feature/test_pipeline`. The chain is
`commands.py` → `session.run_tests` → the module's `run_ctest` → `cmake_driver.ctest_run`
(`ctest --output-junit`) → `budget.py`, which runs `tools/testing/test_budget.py`.

| Rule of `testing` | State | What is missing |
| --- | --- | --- |
| `small` and `medium` by default, `large` only with a filter or `--all` | done | |
| Shuffle with a printed seed and a repeat command | partial | the module's own pytest suite is not shuffled |
| Per-case results from gtest XML | partial | only where a module registers one CTest entry per case |
| Time lines against the limits | partial | the reader never gates, gets no `--programs`, and the limits are `K_TEST_BUDGET` at 1 s and 10 s, not `K_TEST_TIMES` |
| `budget_exemptions.toml` only shrinks | partial | checked within one run only |
| `quarantined` reported and never gating | partial | a quarantined run returns CTest's exit code |
| Shards of about 10 s through `GTEST_TOTAL_SHARDS` and `GTEST_SHARD_INDEX` | missing | no shard is registered or run |
| `RESOURCE_GROUPS gpus:1` on a device shard | missing | no resource file or spec |
| A failed case rerun once alone, a pass on rerun reported flaky, no gating retry | missing | `--repeat` maps to `until-fail` |
| The size ratio printed per module | missing | the reader counts the whole run |
| A skipped size printed and not green | missing | skipped cases are dropped |
| Python and TypeScript in parallel workers | missing | |
| The changed modules and those above them, from the module graph | missing | the graph exists in `provision/closure.py` for dependencies only |

`source/sushicore/testing/README.md` says sushicore has no reader; `tools/testing/test_budget.py`
is there. sushicore's own CI runs pytest directly, not through the command.

## Jobs

| Job | Files | Waits on | Status |
| --- | --- | --- | --- |
| F1 | `tools/` copied fresh from SushiSkills (its job J10), `tools/settings.py` `K_TEST_TIMES` at the `testing` values | | todo |
| F2 | a CMake helper the module builds include, registering one CTest entry per shard with `RESOURCE_GROUPS` for a device program | | todo |
| F3 | `session.py`, `cmake_driver.py`: run shards, collect gtest XML per shard, rerun each failed case once alone, report flaky | F2 | todo |
| F4 | `budget.py` and the reader: `--programs` passed, time and ratio lines per module, a skipped size printed and the run not green, quarantined cases reported and never gating | F1 | todo |
| F5 | `session.py`: `--changed-since <commit>` selects the changed modules and those above them from the module graph | | todo |
| F6 | `session.py`: the module's own pytest suite shuffled with the printed seed and run in parallel workers | | todo |
| F7 | `.github/workflows/ci.yml`: sushicore's own pre-merge through the command's Python path | F6 | todo |
| F8 | `source/sushicore/testing/README.md` and the pages that describe the command | F3, F4, F5, F6 | todo |
| F9 | release of sushicore and the move of each module CLI onto it, one job per repository | F8 | todo |

## Acceptance

- **F1.** `tools/` equals SushiSkills's copy; the reader reads `K_TEST_TIMES`. Build: sushicore's checkers.
- **F2.** One module's test program registers shards of about 10 s, and a device program asks for
  `gpus:1`. Build: that module's CLI configure and test, run by the orchestrator.
- **F3.** A planted failing case is rerun alone once; a planted flaky case is reported flaky and the
  run is red. Build: sushicore's tests, small.
- **F4.** The printed lines name each module with its time and its ratio; a run that skipped a size
  is not green. Build: sushicore's tests, small.
- **F5.** A change to a low module selects it and every module above it, and nothing else. Build:
  sushicore's tests, small.
- **F6.** Two runs with one seed run the cases in one order; workers are used. Build: sushicore's
  tests.
- **F7.** CI runs the command. Build: CI green on the branch.
- **F8.** The pages say what the command does. Build: `check_docs_truth.py`.
- **F9.** Each module CLI runs `test` through the released command. Build: each module's CLI.

## Waiting for the owner

- **F2** adds a public interface: a CMake helper every module build calls. Its name and arguments are
  the owner's.
- **F6** needs a parallel runner. `pytest-xdist` is an external dependency; the alternative is a
  runner of our own that splits the collected cases by the seed into worker processes, with no
  package added. The engineer recommends our own runner.
</content>
</invoke>
